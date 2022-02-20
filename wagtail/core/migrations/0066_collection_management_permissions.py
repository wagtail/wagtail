# -*- coding: utf-8 -*-
from django.db import migrations


def grant_instance_level_collection_management_permissions(apps, schema_editor):
    """
    Give the groups who currently manage all collections permission to manage root collections
    """
    Collection = apps.get_model("wagtailcore.Collection")
    Group = apps.get_model("auth.Group")
    GroupCollectionPermission = apps.get_model("wagtailcore.GroupCollectionPermission")
    Permission = apps.get_model("auth.Permission")

    groups_w_permissions = Group.objects.filter(
        permissions__content_type__app_label="wagtailcore",
        permissions__content_type__model="collection",
        permissions__codename__in=[
            "add_collection",
            "change_collection",
            "delete_collection",
        ],
    ).values("id", "name", "permissions__id", "permissions__codename")

    for root_collection in Collection.objects.filter(depth=1).all():
        for row in groups_w_permissions:
            GroupCollectionPermission.objects.create(
                group_id=row["id"],
                permission_id=row["permissions__id"],
                collection_id=root_collection.id,
            )
    # Now remove the model-level permissions for collections
    collection_permissions = Permission.objects.filter(
        content_type__app_label="wagtailcore",
        content_type__model="collection",
        codename__in=["add_collection", "change_collection", "delete_collection"],
    )
    for perm in collection_permissions.all():
        perm.group_set.clear()


def revert_to_model_level_collection_management_permissions(apps, schema_editor):
    """
    Give model-level permission to all groups who have that permission on the root collection
    """
    Collection = apps.get_model("wagtailcore.Collection")
    GroupCollectionPermission = apps.get_model("wagtailcore.GroupCollectionPermission")

    root_collections = Collection.objects.filter(depth=1).all()
    group_collection_permissions = GroupCollectionPermission.objects.filter(
        permission__content_type__app_label="wagtailcore",
        permission__content_type__model="collection",
        permission__codename__in=[
            "add_collection",
            "change_collection",
            "delete_collection",
        ],
        collection__in=root_collections,
    ).select_related("group", "permission")

    for row in group_collection_permissions.all():
        row.group.permissions.add(row.permission)

    # Now delete the instance-level collection management permissions
    group_collection_permissions.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0065_log_entry_uuid"),
    ]

    operations = [
        migrations.RunPython(
            grant_instance_level_collection_management_permissions,
            revert_to_model_level_collection_management_permissions,
        )
    ]
