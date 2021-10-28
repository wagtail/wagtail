# -*- coding: utf-8 -*-
from django.db import migrations


def get_image_permissions(apps):
    # return a queryset of the 'add_image' and 'change_image' permissions
    Permission = apps.get_model('auth.Permission')
    ContentType = apps.get_model('contenttypes.ContentType')

    image_content_type, _created = ContentType.objects.get_or_create(
        model='image',
        app_label='wagtailimages',
    )
    return Permission.objects.filter(
        content_type=image_content_type,
        codename__in=['add_image', 'change_image']
    )


def copy_image_permissions_to_collections(apps, schema_editor):
    Collection = apps.get_model('wagtailcore.Collection')
    Group = apps.get_model('auth.Group')
    GroupCollectionPermission = apps.get_model('wagtailcore.GroupCollectionPermission')

    root_collection = Collection.objects.get(depth=1)

    for permission in get_image_permissions(apps):
        for group in Group.objects.filter(permissions=permission):
            GroupCollectionPermission.objects.create(
                group=group,
                collection=root_collection,
                permission=permission
            )


def remove_image_permissions_from_collections(apps, schema_editor):
    GroupCollectionPermission = apps.get_model('wagtailcore.GroupCollectionPermission')
    image_permissions = get_image_permissions(apps)

    GroupCollectionPermission.objects.filter(permission__in=image_permissions).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0026_group_collection_permission'),
        ('wagtailimages', '0011_image_collection'),
    ]

    operations = [
        migrations.RunPython(
            copy_image_permissions_to_collections,
            remove_image_permissions_from_collections),
    ]
