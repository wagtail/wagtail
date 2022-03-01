# -*- coding: utf-8 -*-
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0020_add_index_on_page_first_published_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="grouppagepermission",
            name="group",
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                related_name="page_permissions",
                to="auth.Group",
                verbose_name="group",
            ),
        ),
        migrations.AlterField(
            model_name="grouppagepermission",
            name="page",
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                related_name="group_permissions",
                to="wagtailcore.Page",
                verbose_name="page",
            ),
        ),
        migrations.AlterField(
            model_name="grouppagepermission",
            name="permission_type",
            field=models.CharField(
                max_length=20,
                verbose_name="permission type",
                choices=[
                    ("add", "Add/edit pages you own"),
                    ("edit", "Edit any page"),
                    ("publish", "Publish any page"),
                    ("lock", "Lock/unlock any page"),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="page",
            name="content_type",
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                related_name="pages",
                to="contenttypes.ContentType",
                verbose_name="content type",
            ),
        ),
        migrations.AlterField(
            model_name="page",
            name="expire_at",
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text="Please add a date-time in the form YYYY-MM-DD hh:mm.",
                verbose_name="expiry date/time",
            ),
        ),
        migrations.AlterField(
            model_name="page",
            name="expired",
            field=models.BooleanField(
                default=False, editable=False, verbose_name="expired"
            ),
        ),
        migrations.AlterField(
            model_name="page",
            name="first_published_at",
            field=models.DateTimeField(
                null=True,
                db_index=True,
                editable=False,
                verbose_name="first published at",
            ),
        ),
        migrations.AlterField(
            model_name="page",
            name="go_live_at",
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text="Please add a date-time in the form YYYY-MM-DD hh:mm.",
                verbose_name="go live date/time",
            ),
        ),
        migrations.AlterField(
            model_name="page",
            name="has_unpublished_changes",
            field=models.BooleanField(
                default=False, editable=False, verbose_name="has unpublished changes"
            ),
        ),
        migrations.AlterField(
            model_name="page",
            name="latest_revision_created_at",
            field=models.DateTimeField(
                null=True, editable=False, verbose_name="latest revision created at"
            ),
        ),
        migrations.AlterField(
            model_name="page",
            name="live",
            field=models.BooleanField(
                default=True, editable=False, verbose_name="live"
            ),
        ),
        migrations.AlterField(
            model_name="page",
            name="locked",
            field=models.BooleanField(
                default=False, editable=False, verbose_name="locked"
            ),
        ),
        migrations.AlterField(
            model_name="page",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="owned_pages",
                null=True,
                to=settings.AUTH_USER_MODEL,
                editable=False,
                verbose_name="owner",
            ),
        ),
        migrations.AlterField(
            model_name="page",
            name="search_description",
            field=models.TextField(blank=True, verbose_name="search description"),
        ),
        migrations.AlterField(
            model_name="page",
            name="seo_title",
            field=models.CharField(
                max_length=255,
                blank=True,
                help_text="Optional. 'Search Engine Friendly' title. This will appear at the top of the browser window.",
                verbose_name="page title",
            ),
        ),
        migrations.AlterField(
            model_name="page",
            name="show_in_menus",
            field=models.BooleanField(
                default=False,
                help_text="Whether a link to this page will appear in automatically generated menus",
                verbose_name="show in menus",
            ),
        ),
        migrations.AlterField(
            model_name="page",
            name="slug",
            field=models.SlugField(
                max_length=255,
                verbose_name="slug",
                help_text="The name of the page as it will appear in URLs e.g http://domain.com/blog/[my-slug]/",
            ),
        ),
        migrations.AlterField(
            model_name="page",
            name="title",
            field=models.CharField(
                max_length=255,
                help_text="The page title as you'd like it to be seen by the public",
                verbose_name="title",
            ),
        ),
        migrations.AlterField(
            model_name="pagerevision",
            name="approved_go_live_at",
            field=models.DateTimeField(
                null=True, blank=True, verbose_name="approved go live at"
            ),
        ),
        migrations.AlterField(
            model_name="pagerevision",
            name="content_json",
            field=models.TextField(verbose_name="content JSON"),
        ),
        migrations.AlterField(
            model_name="pagerevision",
            name="created_at",
            field=models.DateTimeField(verbose_name="created at"),
        ),
        migrations.AlterField(
            model_name="pagerevision",
            name="page",
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                related_name="revisions",
                to="wagtailcore.Page",
                verbose_name="page",
            ),
        ),
        migrations.AlterField(
            model_name="pagerevision",
            name="submitted_for_moderation",
            field=models.BooleanField(
                default=False, db_index=True, verbose_name="submitted for moderation"
            ),
        ),
        migrations.AlterField(
            model_name="pagerevision",
            name="user",
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                blank=True,
                null=True,
                to=settings.AUTH_USER_MODEL,
                verbose_name="user",
            ),
        ),
        migrations.AlterField(
            model_name="pageviewrestriction",
            name="page",
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                related_name="view_restrictions",
                to="wagtailcore.Page",
                verbose_name="page",
            ),
        ),
        migrations.AlterField(
            model_name="pageviewrestriction",
            name="password",
            field=models.CharField(max_length=255, verbose_name="password"),
        ),
        migrations.AlterField(
            model_name="site",
            name="hostname",
            field=models.CharField(
                max_length=255, db_index=True, verbose_name="hostname"
            ),
        ),
        migrations.AlterField(
            model_name="site",
            name="is_default_site",
            field=models.BooleanField(
                default=False,
                help_text="If true, this site will handle requests for all other hostnames that do not have a site entry of their own",
                verbose_name="is default site",
            ),
        ),
        migrations.AlterField(
            model_name="site",
            name="port",
            field=models.IntegerField(
                default=80,
                help_text="Set this to something other than 80 if you need a specific port number to appear in URLs (e.g. development on port 8000). Does not affect request handling (so port forwarding still works).",
                verbose_name="port",
            ),
        ),
        migrations.AlterField(
            model_name="site",
            name="root_page",
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                related_name="sites_rooted_here",
                to="wagtailcore.Page",
                verbose_name="root page",
            ),
        ),
    ]
