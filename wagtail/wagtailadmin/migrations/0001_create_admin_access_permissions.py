# encoding: utf8
from django.db import models, migrations


def create_admin_access_permissions(apps, schema_editor):
    ContentType = apps.get_model('contenttypes.ContentType')
    Permission = apps.get_model('auth.Permission')
    Group = apps.get_model('auth.Group')

    # Add a fake content type to hang the 'can access Wagtail admin' permission off.
    # The fact that this doesn't correspond to an actual defined model shouldn't matter, I hope...
    wagtailadmin_content_type = ContentType.objects.create(
        app_label='wagtailadmin',
        model='admin',
        name='Wagtail admin'
    )

    # Create admin permission
    admin_permission = Permission.objects.create(
        content_type=wagtailadmin_content_type,
        codename='access_admin',
        name='Can access Wagtail admin'
    )

    # Assign it to Editors and Moderators groups
    for group in Group.objects.filter(name__in=['Editors', 'Moderators']):
        group.permissions.add(admin_permission)


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0005_initial_data'),
    ]

    operations = [
        migrations.RunPython(create_admin_access_permissions),
    ]
