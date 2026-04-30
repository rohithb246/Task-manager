from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone


class Task(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("In Progress", "In Progress"),
        ("Completed", "Completed"),
    ]

    PRIORITY_CHOICES = [
        ("Low", "Low"),
        ("Medium", "Medium"),
        ("High", "High"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    assigned_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assigned_tasks")
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="created_tasks",
        null=True,
        blank=True,
    )
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    deadline = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    progress = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    last_progress_update = models.DateTimeField(null=True, blank=True)
    submission_file = models.FileField(upload_to="task_submissions/", null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        return self.status != "Completed" and self.deadline < timezone.now()

    @property
    def due_within_24_hours(self):
        if self.status == "Completed":
            return False
        now = timezone.now()
        return now <= self.deadline <= now + timezone.timedelta(hours=24)

    @property
    def needs_progress_reminder(self):
        if self.status == "Completed":
            return False
        last_update = self.last_progress_update or self.updated_at
        return last_update < timezone.now() - timezone.timedelta(days=2)


class TaskComment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="task_comments")
    comment = models.TextField()
    progress = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author.username} on {self.task.title}"


class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ("created", "Created"),
        ("assigned", "Assigned"),
        ("status_changed", "Status Changed"),
        ("progress_updated", "Progress Updated"),
        ("comment_added", "Comment Added"),
        ("file_uploaded", "File Uploaded"),
        ("updated", "Updated"),
    ]

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="activity_logs")
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.message
