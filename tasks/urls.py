from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ActivityLogViewSet,
    LoginView,
    LogoutView,
    SignupView,
    TaskCommentViewSet,
    TaskViewSet,
    UserViewSet,
    alerts,
    dashboard,
    me,
)

router = DefaultRouter()
router.register("tasks", TaskViewSet, basename="tasks")
router.register("comments", TaskCommentViewSet, basename="comments")
router.register("activity-logs", ActivityLogViewSet, basename="activity-logs")
router.register("users", UserViewSet, basename="users")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/signup/", SignupView.as_view(), name="signup"),
    path("auth/me/", me, name="me"),
    path("dashboard/", dashboard, name="dashboard"),
    path("alerts/", alerts, name="alerts"),
]
