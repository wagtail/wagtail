# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import migrations, models

import wagtail.search.index


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

    dependencies = [
        ("auth", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contenttypes", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="GroupPagePermission",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        verbose_name="ID",
                        primary_key=True,
                        auto_created=True,
                    ),
                ),
                (
                    "permission_type",
                    models.CharField(
                        choices=[
                            ("add", "Add"),
                            ("edit", "Edit"),
                            ("publish", "Publish"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        to="auth.Group",
                        related_name="page_permissions",
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Page",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        verbose_name="ID",
                        primary_key=True,
                        auto_created=True,
                    ),
                ),
                ("path", models.CharField(max_length=255, unique=True)),
                ("depth", models.PositiveIntegerField()),
                ("numchild", models.PositiveIntegerField(default=0)),
                (
                    "title",
                    models.CharField(
                        max_length=255,
                        help_text="The page title as you'd like it to be seen by the public",
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        help_text="The name of the page as it will appear in URLs e.g http://domain.com/blog/[my-slug]/"
                    ),
                ),
                ("live", models.BooleanField(default=True, editable=False)),
                (
                    "has_unpublished_changes",
                    models.BooleanField(default=False, editable=False),
                ),
                (
                    "url_path",
                    models.CharField(blank=True, max_length=255, editable=False),
                ),
                (
                    "seo_title",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        help_text=(
                            "Optional. 'Search Engine Friendly' title."
                            " This will appear at the top of the browser window."
                        ),
                        verbose_name="Page title",
                    ),
                ),
                (
                    "show_in_menus",
                    models.BooleanField(
                        default=False,
                        help_text="Whether a link to this page will appear in automatically generated menus",
                    ),
                ),
                ("search_description", models.TextField(blank=True)),
                (
                    "go_live_at",
                    models.DateTimeField(
                        blank=True,
                        verbose_name="Go live date/time",
                        null=True,
                        help_text="Please add a date-time in the form YYYY-MM-DD hh:mm:ss.",
                    ),
                ),
                (
                    "expire_at",
                    models.DateTimeField(
                        blank=True,
                        verbose_name="Expiry date/time",
                        null=True,
                        help_text="Please add a date-time in the form YYYY-MM-DD hh:mm:ss.",
                    ),
                ),
                ("expired", models.BooleanField(default=False, editable=False)),
                (
                    "content_type",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        to="contenttypes.ContentType",
                        related_name="pages",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        blank=True,
                        null=True,
                        to=settings.AUTH_USER_MODEL,
                        editable=False,
                        related_name="owned_pages",
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
            name="PageRevision",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        verbose_name="ID",
                        primary_key=True,
                        auto_created=True,
                    ),
                ),
                ("submitted_for_moderation", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("content_json", models.TextField()),
                ("approved_go_live_at", models.DateTimeField(blank=True, null=True)),
                (
                    "page",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        to="wagtailcore.Page",
                        related_name="revisions",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        blank=True,
                        null=True,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="PageViewRestriction",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        verbose_name="ID",
                        primary_key=True,
                        auto_created=True,
                    ),
                ),
                ("password", models.CharField(max_length=255)),
                (
                    "page",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        to="wagtailcore.Page",
                        related_name="view_restrictions",
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Site",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        verbose_name="ID",
                        primary_key=True,
                        auto_created=True,
                    ),
                ),
                ("hostname", models.CharField(max_length=255, db_index=True)),
                (
                    "port",
                    models.IntegerField(
                        default=80,
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
                        to="wagtailcore.Page",
                        related_name="sites_rooted_here",
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name="site",
            unique_together={("hostname", "port")},
        ),
        migrations.AddField(
            model_name="grouppagepermission",
            name="page",
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                to="wagtailcore.Page",
                related_name="group_permissions",
            ),
            preserve_default=True,
        ),
    ]
