# -*- coding: utf-8 -*-
from django.db import migrations


def add_document_permissions_to_admin_groups(apps, schema_editor):
    ContentType = apps.get_model("contenttypes.ContentType")
    Permission = apps.get_model("auth.Permission")
    Group = apps.get_model("auth.Group")

    # Get document permissions
    document_content_type, _created = ContentType.objects.get_or_create(
        model="document", app_label="wagtaildocs"
    )

    add_document_permission, _created = Permission.objects.get_or_create(
        content_type=document_content_type,
        codename="add_document",
        defaults={"name": "Can add document"},
    )
    change_document_permission, _created = Permission.objects.get_or_create(
        content_type=document_content_type,
        codename="change_document",
        defaults={"name": "Can change document"},
    )
    delete_document_permission, _created = Permission.objects.get_or_create(
        content_type=document_content_type,
        codename="delete_document",
        defaults={"name": "Can delete document"},
    )

    # Assign it to Editors and Moderators groups
    for group in Group.objects.filter(name__in=["Editors", "Moderators"]):
        group.permissions.add(
            add_document_permission,
            change_document_permission,
            delete_document_permission,
        )


def remove_document_permissions(apps, schema_editor):
    """Reverse the above additions of permissions."""
    ContentType = apps.get_model("contenttypes.ContentType")
    Permission = apps.get_model("auth.Permission")
    document_content_type = ContentType.objects.get(
        model="document",
        app_label="wagtaildocs",
    )
    # This cascades to Group
    Permission.objects.filter(
        content_type=document_content_type,
        codename__in=("add_document", "change_document", "delete_document"),
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("wagtaildocs", "0001_initial"),
        # Need to run wagtailcores initial data migration to make sure the groups are created
        ("wagtailcore", "0002_initial_data"),
    ]

    operations = [
        migrations.RunPython(
            add_document_permissions_to_admin_groups, remove_document_permissions
        ),
    ]
