# -*- coding: utf-8 -*-
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import wagtail.search.index


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
    Site.objects.get_or_create(
        hostname="localhost", root_page_id=homepage.id, is_default_site=True
    )

    # Create auth groups
    moderators_group, created = Group.objects.get_or_create(name="Moderators")
    editors_group, created = Group.objects.get_or_create(name="Editors")

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

    # 0005 - add_page_lock_permission_to_moderators
    GroupPagePermission.objects.create(
        group=moderators_group,
        page=root,
        permission_type="lock",
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


def set_page_path_collation(apps, schema_editor):
    """
    Treebeard's path comparison logic can fail on certain locales such as sk_SK, which
    sort numbers after letters. To avoid this, we explicitly set the collation for the
    'path' column to the (non-locale-specific) 'C' collation.

    See: https://groups.google.com/d/msg/wagtail/q0leyuCnYWI/I9uDvVlyBAAJ
    """
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(
            """
            ALTER TABLE wagtailcore_page ALTER COLUMN path TYPE VARCHAR(255) COLLATE "C"
        """
        )


class Migration(migrations.Migration):

    replaces = [
        ("wagtailcore", "0001_initial"),
        ("wagtailcore", "0002_initial_data"),
        ("wagtailcore", "0003_add_uniqueness_constraint_on_group_page_permission"),
        ("wagtailcore", "0004_page_locked"),
        ("wagtailcore", "0005_add_page_lock_permission_to_moderators"),
        ("wagtailcore", "0006_add_lock_page_permission"),
        ("wagtailcore", "0007_page_latest_revision_created_at"),
        ("wagtailcore", "0008_populate_latest_revision_created_at"),
        ("wagtailcore", "0009_remove_auto_now_add_from_pagerevision_created_at"),
        ("wagtailcore", "0010_change_page_owner_to_null_on_delete"),
        ("wagtailcore", "0011_page_first_published_at"),
        ("wagtailcore", "0012_extend_page_slug_field"),
        ("wagtailcore", "0013_update_golive_expire_help_text"),
        ("wagtailcore", "0014_add_verbose_name"),
        ("wagtailcore", "0015_add_more_verbose_names"),
        ("wagtailcore", "0016_change_page_url_path_to_text_field"),
    ]

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("auth", "0001_initial"),
        ("contenttypes", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Page",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        verbose_name="ID",
                        serialize=False,
                        primary_key=True,
                    ),
                ),
                ("path", models.CharField(unique=True, max_length=255)),
                ("depth", models.PositiveIntegerField()),
                ("numchild", models.PositiveIntegerField(default=0)),
                (
                    "title",
                    models.CharField(
                        verbose_name="Title",
                        max_length=255,
                        help_text="The page title as you'd like it to be seen by the public",
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        verbose_name="Slug",
                        max_length=255,
                        help_text="The name of the page as it will appear in URLs e.g http://domain.com/blog/[my-slug]/",
                    ),
                ),
                (
                    "live",
                    models.BooleanField(
                        default=True, verbose_name="Live", editable=False
                    ),
                ),
                (
                    "has_unpublished_changes",
                    models.BooleanField(
                        default=False,
                        verbose_name="Has unpublished changes",
                        editable=False,
                    ),
                ),
                (
                    "url_path",
                    models.TextField(
                        verbose_name="URL path", blank=True, editable=False
                    ),
                ),
                (
                    "seo_title",
                    models.CharField(
                        verbose_name="Page title",
                        max_length=255,
                        blank=True,
                        help_text=(
                            "Optional. 'Search Engine Friendly' title."
                            " This will appear at the top of the browser window."
                        ),
                    ),
                ),
                (
                    "show_in_menus",
                    models.BooleanField(
                        default=False,
                        verbose_name="Show in menus",
                        help_text="Whether a link to this page will appear in automatically generated menus",
                    ),
                ),
                (
                    "search_description",
                    models.TextField(verbose_name="Search description", blank=True),
                ),
                (
                    "go_live_at",
                    models.DateTimeField(
                        null=True,
                        verbose_name="Go live date/time",
                        blank=True,
                        help_text="Please add a date-time in the form YYYY-MM-DD hh:mm.",
                    ),
                ),
                (
                    "expire_at",
                    models.DateTimeField(
                        null=True,
                        verbose_name="Expiry date/time",
                        blank=True,
                        help_text="Please add a date-time in the form YYYY-MM-DD hh:mm.",
                    ),
                ),
                (
                    "expired",
                    models.BooleanField(
                        default=False, verbose_name="Expired", editable=False
                    ),
                ),
                (
                    "content_type",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        verbose_name="Content type",
                        related_name="pages",
                        to="contenttypes.ContentType",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        null=True,
                        verbose_name="Owner",
                        blank=True,
                        editable=False,
                        related_name="owned_pages",
                        to=settings.AUTH_USER_MODEL,
                        on_delete=django.db.models.deletion.SET_NULL,
                    ),
                ),
                (
                    "locked",
                    models.BooleanField(
                        default=False, verbose_name="Locked", editable=False
                    ),
                ),
                (
                    "latest_revision_created_at",
                    models.DateTimeField(
                        null=True,
                        verbose_name="Latest revision created at",
                        editable=False,
                    ),
                ),
                (
                    "first_published_at",
                    models.DateTimeField(
                        null=True, verbose_name="First published at", editable=False
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=(wagtail.search.index.Indexed, models.Model),
        ),
        migrations.RunPython(set_page_path_collation, migrations.RunPython.noop),
        migrations.CreateModel(
            name="GroupPagePermission",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        verbose_name="ID",
                        serialize=False,
                        primary_key=True,
                    ),
                ),
                (
                    "permission_type",
                    models.CharField(
                        verbose_name="Permission type",
                        choices=[
                            ("add", "Add/edit pages you own"),
                            ("edit", "Add/edit any page"),
                            ("publish", "Publish any page"),
                            ("lock", "Lock/unlock any page"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        verbose_name="Group",
                        related_name="page_permissions",
                        to="auth.Group",
                    ),
                ),
                (
                    "page",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        verbose_name="Page",
                        related_name="group_permissions",
                        to="wagtailcore.Page",
                    ),
                ),
            ],
        ),
        migrations.AlterUniqueTogether(
            name="grouppagepermission",
            unique_together={("group", "page", "permission_type")},
        ),
        migrations.AlterModelOptions(
            name="grouppagepermission",
            options={"verbose_name": "Group Page Permission"},
        ),
        migrations.CreateModel(
            name="PageRevision",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        verbose_name="ID",
                        serialize=False,
                        primary_key=True,
                    ),
                ),
                (
                    "submitted_for_moderation",
                    models.BooleanField(
                        default=False, verbose_name="Submitted for moderation"
                    ),
                ),
                ("created_at", models.DateTimeField(verbose_name="Created at")),
                ("content_json", models.TextField(verbose_name="Content JSON")),
                (
                    "approved_go_live_at",
                    models.DateTimeField(
                        null=True, verbose_name="Approved go live at", blank=True
                    ),
                ),
                (
                    "page",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        verbose_name="Page",
                        related_name="revisions",
                        to="wagtailcore.Page",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        null=True,
                        verbose_name="User",
                        blank=True,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AlterModelOptions(
            name="pagerevision",
            options={"verbose_name": "Page Revision"},
        ),
        migrations.CreateModel(
            name="PageViewRestriction",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        verbose_name="ID",
                        serialize=False,
                        primary_key=True,
                    ),
                ),
                ("password", models.CharField(verbose_name="Password", max_length=255)),
                (
                    "page",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        verbose_name="Page",
                        related_name="view_restrictions",
                        to="wagtailcore.Page",
                    ),
                ),
            ],
        ),
        migrations.AlterModelOptions(
            name="pageviewrestriction",
            options={"verbose_name": "Page View Restriction"},
        ),
        migrations.CreateModel(
            name="Site",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        verbose_name="ID",
                        serialize=False,
                        primary_key=True,
                    ),
                ),
                (
                    "hostname",
                    models.CharField(
                        verbose_name="Hostname", db_index=True, max_length=255
                    ),
                ),
                (
                    "port",
                    models.IntegerField(
                        default=80,
                        verbose_name="Port",
                        help_text=(
                            "Set this to something other than 80 if you need a specific port number"
                            " to appear in URLs (e.g. development on port 8000)."
                            " Does not affect request handling (so port forwarding still works)."
                        ),
                    ),
                ),
                (
                    "is_default_site",
                    models.BooleanField(
                        default=False,
                        verbose_name="Is default site",
                        help_text=(
                            "If true, this site will handle requests for all other hostnames"
                            " that do not have a site entry of their own"
                        ),
                    ),
                ),
                (
                    "root_page",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        verbose_name="Root page",
                        related_name="sites_rooted_here",
                        to="wagtailcore.Page",
                    ),
                ),
            ],
        ),
        migrations.AlterUniqueTogether(
            name="site",
            unique_together={("hostname", "port")},
        ),
        migrations.AlterModelOptions(
            name="site",
            options={"verbose_name": "Site"},
        ),
        migrations.RunPython(initial_data, remove_initial_data),
    ]
