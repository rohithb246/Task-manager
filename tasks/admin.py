from django.contrib import admin

from .models import ActivityLog, Task, TaskComment


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "assigned_user", "priority", "deadline", "status", "progress")
    list_filter = ("priority", "status", "deadline")
    search_fields = ("title", "description", "assigned_user__username")


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ("task", "author", "progress", "created_at")
    search_fields = ("task__title", "author__username", "comment")


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("task", "actor", "action", "created_at")
    list_filter = ("action", "created_at")
