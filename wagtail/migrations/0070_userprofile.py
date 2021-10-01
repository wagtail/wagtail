# Generated by Django 3.1.8 on 2021-10-01 12:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import wagtail.models.user_profile


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("wagtailcore", "0069_log_entry_jsonfield"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "submitted_notifications",
                    models.BooleanField(
                        default=True,
                        help_text="Receive notification when a page is submitted for moderation",
                        verbose_name="submitted notifications",
                    ),
                ),
                (
                    "approved_notifications",
                    models.BooleanField(
                        default=True,
                        help_text="Receive notification when your page edit is approved",
                        verbose_name="approved notifications",
                    ),
                ),
                (
                    "rejected_notifications",
                    models.BooleanField(
                        default=True,
                        help_text="Receive notification when your page edit is rejected",
                        verbose_name="rejected notifications",
                    ),
                ),
                (
                    "updated_comments_notifications",
                    models.BooleanField(
                        default=True,
                        help_text="Receive notification when comments have been created, resolved, or deleted on a page that you have subscribed to receive comment notifications on",
                        verbose_name="updated comments notifications",
                    ),
                ),
                (
                    "preferred_language",
                    models.CharField(
                        default="",
                        help_text="Select language for the admin",
                        max_length=10,
                        verbose_name="preferred language",
                    ),
                ),
                (
                    "current_time_zone",
                    models.CharField(
                        default="",
                        help_text="Select your current time zone",
                        max_length=40,
                        verbose_name="current time zone",
                    ),
                ),
                (
                    "avatar",
                    models.ImageField(
                        blank=True,
                        upload_to=wagtail.models.user_profile.upload_avatar_to,
                        verbose_name="profile picture",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="wagtail_userprofile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "user profile",
                "verbose_name_plural": "user profiles",
            },
        ),
    ]
