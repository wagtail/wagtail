from django.db import migrations


def initial_data(apps, schema_editor):
    ContentType = apps.get_model("contenttypes.ContentType")
    Group = apps.get_model("auth.Group")
    Page = apps.get_model("wagtailcore.Page")
    Site = apps.get_model("wagtailcore.Site")
    GroupPagePermission = apps.get_model("wagtailcore.GroupPagePermission")

    # Create page content type
    page_content_type, created = ContentType.objects.get_or_create(
        model="page", app_label="wagtailcore"
    )

    # Create root page
    root = Page.objects.create(
        title="Root",
        slug="root",
        content_type=page_content_type,
        path="0001",
        depth=1,
        numchild=1,
        url_path="/",
    )

    # Create homepage
    homepage = Page.objects.create(
        title="Welcome to your new Wagtail site!",
        slug="home",
        content_type=page_content_type,
        path="00010001",
        depth=2,
        numchild=0,
        url_path="/home/",
    )

    # Create default site
    Site.objects.create(
        hostname="localhost", root_page_id=homepage.id, is_default_site=True
    )

    # Create auth groups
    moderators_group = Group.objects.create(name="Moderators")
    editors_group = Group.objects.create(name="Editors")

    # Create group permissions
    GroupPagePermission.objects.create(
        group=moderators_group,
        page=root,
        permission_type="add",
    )
    GroupPagePermission.objects.create(
        group=moderators_group,
        page=root,
        permission_type="edit",
    )
    GroupPagePermission.objects.create(
        group=moderators_group,
        page=root,
        permission_type="publish",
    )

    GroupPagePermission.objects.create(
        group=editors_group,
        page=root,
        permission_type="add",
    )
    GroupPagePermission.objects.create(
        group=editors_group,
        page=root,
        permission_type="edit",
    )


def remove_initial_data(apps, schema_editor):
    """This function does nothing. The below code is commented out together
    with an explanation of why we don't need to bother reversing any of the
    initial data"""
    pass
    # This does not need to be deleted, Django takes care of it.
    # page_content_type = ContentType.objects.get(
    #     model='page',
    #     app_label='wagtailcore',
    # )

    # Page objects: Do nothing, the table will be deleted when reversing 0001

    # Do not reverse Site creation since other models might depend on it

    # Remove auth groups -- is this safe? External objects might depend
    # on these groups... seems unsafe.
    # Group.objects.filter(
    #     name__in=('Moderators', 'Editors')
    # ).delete()
    #
    # Likewise, we're leaving all GroupPagePermission unchanged as users may
    # have been assigned such permissions and its harmless to leave them.


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(initial_data, remove_initial_data),
    ]
