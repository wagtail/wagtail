# -*- coding: utf-8 -*-
from django.db import migrations


def reassign_admin_access_permission(apps, schema_editor):
    ContentType = apps.get_model('contenttypes.ContentType')
    Permission = apps.get_model('auth.Permission')
    Group = apps.get_model('auth.Group')

    # Add a content type to hang the 'can access Wagtail admin' permission off
    admin_content_type, created = ContentType.objects.get_or_create(
        app_label='wagtailcore',
        model='admin'
    )

    try:
        permission = Permission.objects.get(codename='access_admin')
        # wagtail.admin has been used, update the existing permission
        permission.content_type = admin_content_type
        permission.save()
    except Permission.DoesNotExist:
        # wagtail.admin not used, create a new permission

        # Create admin permission
        admin_permission, created = Permission.objects.get_or_create(
            content_type=admin_content_type,
            codename='access_admin',
            name='Can access Wagtail admin'
        )

        # Assign it to Editors and Moderators groups
        for group in Group.objects.filter(name__in=['Editors', 'Moderators']):
            group.permissions.add(admin_permission)


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0069_admin'),
    ]

    operations = [
        migrations.RunPython(reassign_admin_access_permission),
    ]
