# -*- coding: utf-8 -*-
from django.db import migrations


def grant_instance_level_collection_management_permissions(apps, schema_editor):
    Collection = apps.get_model('wagtailcore.Collection')
    GroupCollectionPermission = apps.get_model('wagtailcore.GroupCollectionPermission')
    Permission = apps.get_model('auth.Permission')

    # Give all groups who currently manage collections permission to manage root collection
    root_collection = Collection.objects.filter(depth=1).order_by('path').first()
    stock_permissions = Permission.objects.filter(
        content_type__app_label='wagtailcore',
        content_type__model='collection',
        codename__in=['add_collection', 'change_collection', 'delete_collection']
    ).prefetch_related('group_set').all()

    for perm in stock_permissions:
        for group in perm.group_set.all():
            gcp = GroupCollectionPermission(
                group_id=group.id,
                collection_id=root_collection.id,
                permission_id=perm.id
            )
            gcp.full_clean()
            gcp.save()
            # Now remove the model-level permissions from the group
            group.permissions.remove(perm)


def revert_to_model_level_collection_management_permissions(apps, schema_editor):
    Collection = apps.get_model('wagtailcore.Collection')
    ContentType = apps.get_model('contenttypes.ContentType')
    GroupCollectionPermission = apps.get_model('wagtailcore.GroupCollectionPermission')
    Permission = apps.get_model('auth.Permission')

    collection_content_type = ContentType.objects.get(
        model='collection',
        app_label='wagtailcore'
    )
    root_collection = Collection.objects.filter(depth=1).order_by('path').first()
    stock_permissions = Permission.objects.filter(
        content_type__app_label='wagtailcore',
        content_type__model='collection',
        codename__in=['add_collection', 'change_collection', 'delete_collection']
    ).all()

    # Give model-level permissions to all groups who have permission on the root collection
    group_collection_permissions = GroupCollectionPermission.objects.filter(
        collection=root_collection,
        permission__in=stock_permissions
    ).prefetch_related('group')

    for row in group_collection_permissions.all():
        perm = Permission.objects.get(
            content_type=collection_content_type,
            codename=row.permission.codename
        )
        row.group.permissions.add(perm)

    # Now delete the instance-level collection management permissions
    group_collection_permissions.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0065_log_entry_uuid'),
    ]

    operations = [
        migrations.RunPython(
            grant_instance_level_collection_management_permissions,
            revert_to_model_level_collection_management_permissions
        )
    ]
