import swapper
from django.db import migrations, models



def populate_page_choose_permission(apps, schema_editor):
    ContentType = apps.get_model("contenttypes.ContentType")
    Permission = apps.get_model("auth.Permission")
    GroupPagePermission = apps.get_model("wagtailcore.GroupPagePermission")
    Group = apps.get_model("auth.Group")
    Page = apps.get_model(swapper.get_model_name("wagtailcore", "Page"))
    page_type = ContentType.objects.get_by_natural_key(Page._meta.app_label, Page._meta.model_name)
    page_choose_permission, created = Permission.objects.get_or_create(
        content_type=page_type,
        codename=f"choose_{Page._meta.model_name}",
        defaults={"name": "Choose pages"},
    )
    root_pages = list(Page.objects.filter(depth=1))
    admin_groups = Group.objects.filter(permissions__codename="access_admin")

    # Assign page choose permission at the root level to all groups that have access to the admin
    for group in admin_groups:
        for root_page in root_pages:
            GroupPagePermission.objects.create(
                group=group,
                page=root_page,
                permission=page_choose_permission,
            )


def delete_page_choose_permission(apps, schema_editor):
    ContentType = apps.get_model("contenttypes.ContentType")
    Permission = apps.get_model("auth.Permission")
    Page = apps.get_model(swapper.get_model_name("wagtailcore", "Page"))
    GroupPagePermission = apps.get_model("wagtailcore.GroupPagePermission")
    page_type = ContentType.objects.get_by_natural_key(Page._meta.app_label, Page._meta.model_name)
    page_choose_permission = Permission.objects.get(
        content_type=page_type,
        codename=f"choose_{Page._meta.model_name}"
    )
    GroupPagePermission.objects.filter(
        permission=page_choose_permission
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailadmin", "0006_formstate"),
        ("wagtailcore", "0099_add_page_choose_permission"),
    ]

    operations = [
        migrations.RunPython(
            populate_page_choose_permission,
            delete_page_choose_permission,
        ),
    ]
