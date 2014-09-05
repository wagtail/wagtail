# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def add_image_permissions_to_admin_groups(apps, schema_editor):
    ContentType = apps.get_model('contenttypes.ContentType')
    Permission = apps.get_model('auth.Permission')
    Group = apps.get_model('auth.Group')
    Image = apps.get_model('wagtailimages.Image')

    # Get image permissions
    image_content_type, _created = ContentType.objects.get_or_create(
        model='image',
        app_label='wagtailimages',
        defaults={'name': 'image'}
    )

    add_image_permission, _created = Permission.objects.get_or_create(
        content_type=image_content_type,
        codename='add_image',
        defaults={'name': 'Can add image'}
    )
    change_image_permission, _created = Permission.objects.get_or_create(
        content_type=image_content_type,
        codename='change_image',
        defaults={'name': 'Can change image'}
    )
    delete_image_permission, _created = Permission.objects.get_or_create(
        content_type=image_content_type,
        codename='delete_image',
        defaults={'name': 'Can delete image'}
    )

    # Assign it to Editors and Moderators groups
    for group in Group.objects.filter(name__in=['Editors', 'Moderators']):
        group.permissions.add(add_image_permission, change_image_permission, delete_image_permission)


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0001_initial'),

        # Need to run wagtailcores initial data migration to make sure the groups are created
        ('wagtailcore', '0002_initial_data'),
    ]

    operations = [
        migrations.RunPython(add_image_permissions_to_admin_groups),
    ]
