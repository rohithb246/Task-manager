from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Avg, Case, Count, IntegerField, Q, Value, When
from django.utils import timezone
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ActivityLog, Task, TaskComment
from .serializers import (
    ActivityLogSerializer,
    SignupSerializer,
    TaskCommentSerializer,
    TaskSerializer,
    UserSerializer,
)


class IsAdminOrAssignedIntern(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.assigned_user == request.user


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({"detail": "Invalid username or password."}, status=status.HTTP_400_BAD_REQUEST)
        login(request, user)
        return Response(UserSerializer(user).data)


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({"detail": "Logged out."})


class SignupView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def me(request):
    return Response(UserSerializer(request.user).data)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return User.objects.order_by("username")
        return User.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def create_intern(self, request):
        username = request.data.get("username", "").strip()
        password = request.data.get("password", "")
        email = request.data.get("email", "").strip()
        if not username or not password:
            return Response(
                {"detail": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(username=username).exists():
            return Response(
                {"detail": "A user with this username already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = User.objects.create_user(username=username, password=password, email=email)
        user.is_staff = False
        user.save(update_fields=["is_staff"])
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], permission_classes=[permissions.IsAdminUser])
    def delete_intern(self, request, pk=None):
        user = self.get_object()
        if user.is_staff:
            return Response(
                {"detail": "Admin accounts cannot be deleted from Intern Performance."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        username = user.username
        user.delete()
        return Response({"detail": f"Intern '{username}' deleted."}, status=status.HTTP_200_OK)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrAssignedIntern]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        queryset = Task.objects.select_related("assigned_user", "created_by").prefetch_related(
            "comments__author",
            "activity_logs__actor",
        )
        if not self.request.user.is_staff:
            queryset = queryset.filter(assigned_user=self.request.user)

        search = self.request.query_params.get("search")
        status_filter = self.request.query_params.get("status")
        priority = self.request.query_params.get("priority")
        deadline = self.request.query_params.get("deadline")

        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if priority:
            queryset = queryset.filter(priority=priority)
        if deadline == "overdue":
            queryset = queryset.filter(deadline__lt=timezone.now()).exclude(status="Completed")
        elif deadline == "next24":
            queryset = queryset.filter(deadline__range=(timezone.now(), timezone.now() + timezone.timedelta(hours=24)))

        return queryset.annotate(
            priority_rank=Case(
                When(priority="High", then=Value(3)),
                When(priority="Medium", then=Value(2)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by("-priority_rank", "deadline")

    def perform_create(self, serializer):
        task = serializer.save(created_by=self.request.user)
        ActivityLog.objects.create(
            task=task,
            actor=self.request.user,
            action="created",
            message=f"{self.request.user.username} created task '{task.title}'.",
        )
        ActivityLog.objects.create(
            task=task,
            actor=self.request.user,
            action="assigned",
            message=f"Task assigned to {task.assigned_user.username}.",
        )

    def perform_update(self, serializer):
        original = self.get_object()
        original_status = original.status
        original_progress = original.progress
        original_assigned_user = original.assigned_user
        task = serializer.save()
        messages = []
        if original_status != task.status:
            messages.append(("status_changed", f"Status changed from {original_status} to {task.status}."))
        if original_progress != task.progress:
            messages.append(("progress_updated", f"Progress updated from {original_progress}% to {task.progress}%."))
        if original_assigned_user != task.assigned_user:
            messages.append(("assigned", f"Task reassigned to {task.assigned_user.username}."))
        if not messages:
            messages.append(("updated", f"{self.request.user.username} updated the task."))
        for action_name, message in messages:
            ActivityLog.objects.create(task=task, actor=self.request.user, action=action_name, message=message)

    @action(detail=True, methods=["post"])
    def comment(self, request, pk=None):
        task = self.get_object()
        serializer = TaskCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(task=task, author=request.user)
        if comment.progress is not None:
            task.progress = comment.progress
            task.last_progress_update = timezone.now()
            task.save(update_fields=["progress", "last_progress_update", "updated_at"])
        ActivityLog.objects.create(
            task=task,
            actor=request.user,
            action="comment_added",
            message=f"{request.user.username} added a progress comment.",
        )
        return Response(TaskCommentSerializer(comment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def upload_submission(self, request, pk=None):
        task = self.get_object()
        if request.user.is_staff:
            return Response(
                {"detail": "Admins cannot upload intern submissions."},
                status=status.HTTP_403_FORBIDDEN,
            )
        uploaded_file = request.FILES.get("file")
        if uploaded_file is None:
            return Response({"detail": "Please choose a file to upload."}, status=status.HTTP_400_BAD_REQUEST)

        task.submission_file = uploaded_file
        task.status = "Completed"
        task.progress = 100
        task.last_progress_update = timezone.now()
        task.submitted_at = timezone.now()
        task.save(
            update_fields=[
                "submission_file",
                "status",
                "progress",
                "last_progress_update",
                "submitted_at",
                "updated_at",
            ]
        )
        ActivityLog.objects.create(
            task=task,
            actor=request.user,
            action="file_uploaded",
            message=f"{request.user.username} uploaded a file and completed the task.",
        )
        return Response(TaskSerializer(task, context={"request": request}).data, status=status.HTTP_200_OK)


class TaskCommentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TaskCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = TaskComment.objects.select_related("task", "author")
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(task__assigned_user=self.request.user)


class ActivityLogViewSet(mixins.DestroyModelMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ActivityLog.objects.select_related("task", "actor")
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(task__assigned_user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response(
                {"detail": "Only admins can delete activity logs."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def dashboard(request):
    base = Task.objects.all() if request.user.is_staff else Task.objects.filter(assigned_user=request.user)
    now = timezone.now()
    status_counts = dict(base.values_list("status").annotate(total=Count("id")))
    total = base.count()
    completed = status_counts.get("Completed", 0)
    overdue = base.filter(deadline__lt=now).exclude(status="Completed").count()
    high_priority = base.filter(priority="High").exclude(status="Completed").count()
    avg_progress = base.aggregate(avg=Avg("progress"))["avg"] or 0

    payload = {
        "total_tasks": total,
        "status_counts": status_counts,
        "overdue_tasks": overdue,
        "high_priority_open": high_priority,
        "average_progress": round(avg_progress, 1),
        "completion_rate": round((completed / total) * 100, 1) if total else 0,
    }

    if request.user.is_staff:
        payload["interns"] = [
            {
                "id": row["assigned_user"],
                "username": row["assigned_user__username"],
                "total": row["total"],
                "completed": row["completed"],
                "avg_progress": round(row["avg_progress"] or 0, 1),
            }
            for row in base.values("assigned_user", "assigned_user__username").annotate(
                total=Count("id"),
                completed=Count("id", filter=Q(status="Completed")),
                avg_progress=Avg("progress"),
            )
        ]

    return Response(payload)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def alerts(request):
    base = Task.objects.all() if request.user.is_staff else Task.objects.filter(assigned_user=request.user)
    now = timezone.now()
    warning_deadline = now + timezone.timedelta(hours=24)
    overdue_tasks = base.filter(deadline__lt=now).exclude(status="Completed")
    due_soon = base.filter(deadline__range=(now, warning_deadline)).exclude(status="Completed")
    inactivity = base.filter(updated_at__lt=now - timezone.timedelta(days=2)).exclude(status="Completed")

    return Response(
        {
            "overdue": TaskSerializer(overdue_tasks, many=True).data,
            "due_soon": TaskSerializer(due_soon, many=True).data,
            "inactivity": TaskSerializer(inactivity, many=True).data,
        }
    )
