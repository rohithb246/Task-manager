from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tasks", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="submission_file",
            field=models.FileField(blank=True, null=True, upload_to="task_submissions/"),
        ),
        migrations.AddField(
            model_name="task",
            name="submitted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="activitylog",
            name="action",
            field=models.CharField(
                choices=[
                    ("created", "Created"),
                    ("assigned", "Assigned"),
                    ("status_changed", "Status Changed"),
                    ("progress_updated", "Progress Updated"),
                    ("comment_added", "Comment Added"),
                    ("file_uploaded", "File Uploaded"),
                    ("updated", "Updated"),
                ],
                max_length=30,
            ),
        ),
    ]
