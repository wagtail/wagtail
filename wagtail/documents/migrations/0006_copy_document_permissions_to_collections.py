# -*- coding: utf-8 -*-
from django.db import migrations


def get_document_permissions(apps):
    # return a queryset of the 'add_document' and 'change_document' permissions
    Permission = apps.get_model('auth.Permission')
    ContentType = apps.get_model('contenttypes.ContentType')

    document_content_type, _created = ContentType.objects.get_or_create(
        model='document',
        app_label='wagtaildocs',
    )
    return Permission.objects.filter(
        content_type=document_content_type,
        codename__in=['add_document', 'change_document']
    )


def copy_document_permissions_to_collections(apps, schema_editor):
    Collection = apps.get_model('wagtailcore.Collection')
    Group = apps.get_model('auth.Group')
    GroupCollectionPermission = apps.get_model('wagtailcore.GroupCollectionPermission')

    root_collection = Collection.objects.get(depth=1)

    for permission in get_document_permissions(apps):
        for group in Group.objects.filter(permissions=permission):
            GroupCollectionPermission.objects.create(
                group=group,
                collection=root_collection,
                permission=permission
            )


def remove_document_permissions_from_collections(apps, schema_editor):
    GroupCollectionPermission = apps.get_model('wagtailcore.GroupCollectionPermission')
    document_permissions = get_document_permissions(apps)

    GroupCollectionPermission.objects.filter(permission__in=document_permissions).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0026_group_collection_permission'),
        ('wagtaildocs', '0005_document_collection'),
    ]

    operations = [
        migrations.RunPython(
            copy_document_permissions_to_collections,
            remove_document_permissions_from_collections),
    ]
