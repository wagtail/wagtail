# Generated by Django 3.1.2 on 2020-10-15 00:52

from django.db import migrations


def add_choose_permission_to_admin_groups(apps, _schema_editor):
    ContentType = apps.get_model('contenttypes.ContentType')
    Permission = apps.get_model('auth.Permission')
    Group = apps.get_model('auth.Group')

    # Get document content type
    document_content_type, _created = ContentType.objects.get_or_create(
        model='document',
        app_label='wagtaildocs'
    )

    # Create the Choose permission (if it doesn't already exist)
    choose_document_permission, _created = Permission.objects.get_or_create(
        content_type=document_content_type,
        codename='choose_document',
        defaults={'name': 'Can choose document'}
    )

    # Assign it to all groups which have "Access the Wagtail admin" permission.
    # This emulates the previous behavior, where everyone who would access the admin
    # could choose any document in any Collection, because choosing wasn't permissioned.
    for group in Group.objects.filter(permissions__codename='access_admin'):
        group.permissions.add(choose_document_permission)


def remove_choose_permission(apps, _schema_editor):
    """Reverse the above additions of permissions."""
    ContentType = apps.get_model('contenttypes.ContentType')
    Permission = apps.get_model('auth.Permission')
    document_content_type = ContentType.objects.get(
        model='document',
        app_label='wagtaildocs',
    )
    # This cascades to Group
    Permission.objects.filter(
        content_type=document_content_type,
        codename='choose_document'
    ).delete()


def get_choose_permission(apps):
    Permission = apps.get_model('auth.Permission')
    ContentType = apps.get_model('contenttypes.ContentType')

    document_content_type, _created = ContentType.objects.get_or_create(
        model='document',
        app_label='wagtaildocs',
    )
    return Permission.objects.filter(
        content_type=document_content_type,
        codename__in=['choose_document']
    )


def copy_choose_permission_to_collections(apps, _schema_editor):
    Collection = apps.get_model('wagtailcore.Collection')
    Group = apps.get_model('auth.Group')
    GroupCollectionPermission = apps.get_model('wagtailcore.GroupCollectionPermission')

    root_collection = Collection.objects.get(depth=1)

    for permission in get_choose_permission(apps):
        for group in Group.objects.filter(permissions=permission):
            GroupCollectionPermission.objects.create(
                group=group,
                collection=root_collection,
                permission=permission
            )


def remove_choose_permission_from_collections(apps, _schema_editor):
    GroupCollectionPermission = apps.get_model('wagtailcore.GroupCollectionPermission')
    choose_permission = get_choose_permission(apps)

    GroupCollectionPermission.objects.filter(permission=choose_permission).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('wagtaildocs', '0010_document_file_hash'),
    ]

    operations = [
        migrations.RunPython(add_choose_permission_to_admin_groups, remove_choose_permission),
        migrations.RunPython(copy_choose_permission_to_collections, remove_choose_permission_from_collections),
    ]
