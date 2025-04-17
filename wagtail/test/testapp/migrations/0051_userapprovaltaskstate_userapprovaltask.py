# Generated by Django 5.1.6 on 2025-02-26 12:17

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tests", "0050_headcountrelatedmodelusingpk_related_page"),
        ("wagtailcore", "0094_alter_page_locale"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserApprovalTaskState",
            fields=[
                (
                    "taskstate_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="wagtailcore.taskstate",
                    ),
                ),
            ],
            bases=("wagtailcore.taskstate",),
        ),
        migrations.CreateModel(
            name="UserApprovalTask",
            fields=[
                (
                    "task_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="wagtailcore.task",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            bases=("wagtailcore.task",),
        ),
    ]
