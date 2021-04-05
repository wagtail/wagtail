from django.db import migrations
from django.db.migrations import RunPython


def add_submit_translation_permission_to_groups(apps, schema_editor):
    ContentType = apps.get_model("contenttypes.ContentType")
    Permission = apps.get_model("auth.Permission")
    Group = apps.get_model("auth.Group")

    content_type, _ = ContentType.objects.get_or_create(
        app_label="simple_translation",
        model="simpletranslation",
    )
    submit_permission, _ = Permission.objects.get_or_create(
        content_type=content_type, codename="submit_translation"
    )
    for group in Group.objects.filter(name__in=["Editors", "Moderators"]):
        group.permissions.add(submit_permission)


class Migration(migrations.Migration):
    dependencies = [
        ("simple_translation", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            add_submit_translation_permission_to_groups, RunPython.noop
        ),
    ]
