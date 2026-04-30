from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers

from .models import ActivityLog, Task, TaskComment


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "is_staff", "role"]

    def get_role(self, obj):
        return "admin" if obj.is_staff else "intern"


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    role = serializers.ChoiceField(choices=["admin", "intern"], default="intern", write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "first_name", "last_name", "role"]

    def create(self, validated_data):
        role = validated_data.pop("role", "intern")
        user = User.objects.create_user(**validated_data)
        user.is_staff = role == "admin"
        user.save(update_fields=["is_staff"])
        return user


class TaskCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = TaskComment
        fields = ["id", "task", "author", "comment", "progress", "created_at"]
        read_only_fields = ["task", "author", "created_at"]


class ActivityLogSerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)

    class Meta:
        model = ActivityLog
        fields = ["id", "task", "actor", "action", "message", "created_at"]


class TaskSerializer(serializers.ModelSerializer):
    assigned_user_detail = UserSerializer(source="assigned_user", read_only=True)
    created_by_detail = UserSerializer(source="created_by", read_only=True)
    comments = TaskCommentSerializer(many=True, read_only=True)
    activity_logs = ActivityLogSerializer(many=True, read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    due_within_24_hours = serializers.BooleanField(read_only=True)
    needs_progress_reminder = serializers.BooleanField(read_only=True)
    submission_file_url = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "assigned_user",
            "assigned_user_detail",
            "created_by",
            "created_by_detail",
            "priority",
            "deadline",
            "status",
            "progress",
            "last_progress_update",
            "submission_file",
            "submission_file_url",
            "submitted_at",
            "created_at",
            "updated_at",
            "comments",
            "activity_logs",
            "is_overdue",
            "due_within_24_hours",
            "needs_progress_reminder",
        ]
        read_only_fields = [
            "created_by",
            "last_progress_update",
            "submission_file",
            "submission_file_url",
            "submitted_at",
            "created_at",
            "updated_at",
        ]

    def get_submission_file_url(self, obj):
        if not obj.submission_file:
            return None
        request = self.context.get("request")
        url = obj.submission_file.url
        return request.build_absolute_uri(url) if request else url

    def validate_progress(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Progress must be between 0 and 100.")
        return value

    def update(self, instance, validated_data):
        if "progress" in validated_data and validated_data["progress"] != instance.progress:
            instance.last_progress_update = timezone.now()
        return super().update(instance, validated_data)
