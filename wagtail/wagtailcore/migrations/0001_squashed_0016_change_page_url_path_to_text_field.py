# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.db.models.deletion
import wagtail.wagtailsearch.index


# Functions from the following migrations need manual copying.
# Move them and any dependencies into this file, then update the
# RunPython operations to refer to the local versions:
# wagtail.wagtailcore.migrations.0005_add_page_lock_permission_to_moderators
# wagtail.wagtailcore.migrations.0002_initial_data
# wagtail.wagtailcore.migrations.0008_populate_latest_revision_created_at

class Migration(migrations.Migration):

    replaces = [('wagtailcore', '0001_initial'), ('wagtailcore', '0002_initial_data'), ('wagtailcore', '0003_add_uniqueness_constraint_on_group_page_permission'), ('wagtailcore', '0004_page_locked'), ('wagtailcore', '0005_add_page_lock_permission_to_moderators'), ('wagtailcore', '0006_add_lock_page_permission'), ('wagtailcore', '0007_page_latest_revision_created_at'), ('wagtailcore', '0008_populate_latest_revision_created_at'), ('wagtailcore', '0009_remove_auto_now_add_from_pagerevision_created_at'), ('wagtailcore', '0010_change_page_owner_to_null_on_delete'), ('wagtailcore', '0011_page_first_published_at'), ('wagtailcore', '0012_extend_page_slug_field'), ('wagtailcore', '0013_update_golive_expire_help_text'), ('wagtailcore', '0014_add_verbose_name'), ('wagtailcore', '0015_add_more_verbose_names'), ('wagtailcore', '0016_change_page_url_path_to_text_field')]

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0001_initial'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupPagePermission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('permission_type', models.CharField(choices=[('add', 'Add'), ('edit', 'Edit'), ('publish', 'Publish')], max_length=20)),
                ('group', models.ForeignKey(related_name='page_permissions', to='auth.Group')),
            ],
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('path', models.CharField(max_length=255, unique=True)),
                ('depth', models.PositiveIntegerField()),
                ('numchild', models.PositiveIntegerField(default=0)),
                ('title', models.CharField(max_length=255, help_text="The page title as you'd like it to be seen by the public")),
                ('slug', models.SlugField(help_text='The name of the page as it will appear in URLs e.g http://domain.com/blog/[my-slug]/')),
                ('live', models.BooleanField(editable=False, default=True)),
                ('has_unpublished_changes', models.BooleanField(editable=False, default=False)),
                ('url_path', models.CharField(max_length=255, editable=False, blank=True)),
                ('seo_title', models.CharField(verbose_name='Page title', max_length=255, blank=True, help_text="Optional. 'Search Engine Friendly' title. This will appear at the top of the browser window.")),
                ('show_in_menus', models.BooleanField(default=False, help_text='Whether a link to this page will appear in automatically generated menus')),
                ('search_description', models.TextField(blank=True)),
                ('go_live_at', models.DateTimeField(verbose_name='Go live date/time', null=True, blank=True, help_text='Please add a date-time in the form YYYY-MM-DD hh:mm:ss.')),
                ('expire_at', models.DateTimeField(verbose_name='Expiry date/time', null=True, blank=True, help_text='Please add a date-time in the form YYYY-MM-DD hh:mm:ss.')),
                ('expired', models.BooleanField(editable=False, default=False)),
                ('content_type', models.ForeignKey(related_name='pages', to='contenttypes.ContentType')),
                ('owner', models.ForeignKey(related_name='owned_pages', editable=False, null=True, to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, wagtail.wagtailsearch.index.Indexed),
        ),
        migrations.CreateModel(
            name='PageRevision',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('submitted_for_moderation', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('content_json', models.TextField()),
                ('approved_go_live_at', models.DateTimeField(null=True, blank=True)),
                ('page', models.ForeignKey(related_name='revisions', to='wagtailcore.Page')),
                ('user', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='PageViewRestriction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('password', models.CharField(max_length=255)),
                ('page', models.ForeignKey(related_name='view_restrictions', to='wagtailcore.Page')),
            ],
        ),
        migrations.CreateModel(
            name='Site',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('hostname', models.CharField(db_index=True, max_length=255)),
                ('port', models.IntegerField(default=80, help_text='Set this to something other than 80 if you need a specific port number to appear in URLs (e.g. development on port 8000). Does not affect request handling (so port forwarding still works).')),
                ('is_default_site', models.BooleanField(default=False, help_text='If true, this site will handle requests for all other hostnames that do not have a site entry of their own')),
                ('root_page', models.ForeignKey(related_name='sites_rooted_here', to='wagtailcore.Page')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='site',
            unique_together=set([('hostname', 'port')]),
        ),
        migrations.AddField(
            model_name='grouppagepermission',
            name='page',
            field=models.ForeignKey(related_name='group_permissions', to='wagtailcore.Page'),
        ),
        migrations.RunPython(
            code=wagtail.wagtailcore.migrations.0002_initial_data.initial_data,
        ),
        migrations.AlterField(
            model_name='grouppagepermission',
            name='permission_type',
            field=models.CharField(choices=[(b'add', b'Add/edit pages you own'), (b'edit', b'Add/edit any page'), (b'publish', b'Publish any page')], max_length=20),
        ),
        migrations.AlterUniqueTogether(
            name='grouppagepermission',
            unique_together=set([('group', 'page', 'permission_type')]),
        ),
        migrations.AddField(
            model_name='page',
            name='locked',
            field=models.BooleanField(editable=False, default=False),
        ),
        migrations.RunPython(
            code=wagtail.wagtailcore.migrations.0005_add_page_lock_permission_to_moderators.add_page_lock_permission_to_moderators,
        ),
        migrations.AlterField(
            model_name='grouppagepermission',
            name='permission_type',
            field=models.CharField(choices=[('add', 'Add/edit pages you own'), ('edit', 'Add/edit any page'), ('publish', 'Publish any page'), ('lock', 'Lock/unlock any page')], max_length=20),
        ),
        migrations.AddField(
            model_name='page',
            name='latest_revision_created_at',
            field=models.DateTimeField(null=True, editable=False),
        ),
        migrations.RunPython(
            code=wagtail.wagtailcore.migrations.0008_populate_latest_revision_created_at.populate_latest_revision_created_at,
        ),
        migrations.AlterField(
            model_name='pagerevision',
            name='created_at',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='page',
            name='owner',
            field=models.ForeignKey(related_name='owned_pages', editable=False, null=True, to=settings.AUTH_USER_MODEL, blank=True, on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AddField(
            model_name='page',
            name='first_published_at',
            field=models.DateTimeField(verbose_name='First published at', null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='page',
            name='slug',
            field=models.SlugField(max_length=255, help_text='The name of the page as it will appear in URLs e.g http://domain.com/blog/[my-slug]/'),
        ),
        migrations.AlterField(
            model_name='page',
            name='expire_at',
            field=models.DateTimeField(verbose_name='Expiry date/time', null=True, blank=True, help_text='Please add a date-time in the form YYYY-MM-DD hh:mm.'),
        ),
        migrations.AlterField(
            model_name='page',
            name='go_live_at',
            field=models.DateTimeField(verbose_name='Go live date/time', null=True, blank=True, help_text='Please add a date-time in the form YYYY-MM-DD hh:mm.'),
        ),
        migrations.AlterField(
            model_name='grouppagepermission',
            name='group',
            field=models.ForeignKey(related_name='page_permissions', to='auth.Group', verbose_name='Group'),
        ),
        migrations.AlterField(
            model_name='grouppagepermission',
            name='page',
            field=models.ForeignKey(related_name='group_permissions', to='wagtailcore.Page', verbose_name='Page'),
        ),
        migrations.AlterField(
            model_name='grouppagepermission',
            name='permission_type',
            field=models.CharField(choices=[('add', 'Add/edit pages you own'), ('edit', 'Add/edit any page'), ('publish', 'Publish any page'), ('lock', 'Lock/unlock any page')], verbose_name='Permission type', max_length=20),
        ),
        migrations.AlterField(
            model_name='page',
            name='search_description',
            field=models.TextField(verbose_name='Search description', blank=True),
        ),
        migrations.AlterField(
            model_name='page',
            name='show_in_menus',
            field=models.BooleanField(verbose_name='Show in menus', default=False, help_text='Whether a link to this page will appear in automatically generated menus'),
        ),
        migrations.AlterField(
            model_name='page',
            name='slug',
            field=models.SlugField(verbose_name='Slug', max_length=255, help_text='The name of the page as it will appear in URLs e.g http://domain.com/blog/[my-slug]/'),
        ),
        migrations.AlterField(
            model_name='page',
            name='title',
            field=models.CharField(verbose_name='Title', max_length=255, help_text="The page title as you'd like it to be seen by the public"),
        ),
        migrations.AlterField(
            model_name='pageviewrestriction',
            name='page',
            field=models.ForeignKey(related_name='view_restrictions', to='wagtailcore.Page', verbose_name='Page'),
        ),
        migrations.AlterField(
            model_name='pageviewrestriction',
            name='password',
            field=models.CharField(verbose_name='Password', max_length=255),
        ),
        migrations.AlterField(
            model_name='site',
            name='hostname',
            field=models.CharField(db_index=True, verbose_name='Hostname', max_length=255),
        ),
        migrations.AlterField(
            model_name='site',
            name='is_default_site',
            field=models.BooleanField(verbose_name='Is default site', default=False, help_text='If true, this site will handle requests for all other hostnames that do not have a site entry of their own'),
        ),
        migrations.AlterField(
            model_name='site',
            name='port',
            field=models.IntegerField(verbose_name='Port', default=80, help_text='Set this to something other than 80 if you need a specific port number to appear in URLs (e.g. development on port 8000). Does not affect request handling (so port forwarding still works).'),
        ),
        migrations.AlterField(
            model_name='site',
            name='root_page',
            field=models.ForeignKey(related_name='sites_rooted_here', to='wagtailcore.Page', verbose_name='Root page'),
        ),
        migrations.AlterModelOptions(
            name='grouppagepermission',
            options={'verbose_name': 'Group Page Permission'},
        ),
        migrations.AlterModelOptions(
            name='pagerevision',
            options={'verbose_name': 'Page Revision'},
        ),
        migrations.AlterModelOptions(
            name='pageviewrestriction',
            options={'verbose_name': 'Page View Restriction'},
        ),
        migrations.AlterModelOptions(
            name='site',
            options={'verbose_name': 'Site'},
        ),
        migrations.AlterField(
            model_name='page',
            name='content_type',
            field=models.ForeignKey(related_name='pages', to='contenttypes.ContentType', verbose_name='Content type'),
        ),
        migrations.AlterField(
            model_name='page',
            name='expired',
            field=models.BooleanField(verbose_name='Expired', editable=False, default=False),
        ),
        migrations.AlterField(
            model_name='page',
            name='has_unpublished_changes',
            field=models.BooleanField(verbose_name='Has unpublished changes', editable=False, default=False),
        ),
        migrations.AlterField(
            model_name='page',
            name='latest_revision_created_at',
            field=models.DateTimeField(verbose_name='Latest revision created at', null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='page',
            name='live',
            field=models.BooleanField(verbose_name='Live', editable=False, default=True),
        ),
        migrations.AlterField(
            model_name='page',
            name='locked',
            field=models.BooleanField(verbose_name='Locked', editable=False, default=False),
        ),
        migrations.AlterField(
            model_name='page',
            name='owner',
            field=models.ForeignKey(related_name='owned_pages', to=settings.AUTH_USER_MODEL, editable=False, verbose_name='Owner', null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AlterField(
            model_name='page',
            name='url_path',
            field=models.CharField(verbose_name='URL path', max_length=255, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='pagerevision',
            name='approved_go_live_at',
            field=models.DateTimeField(verbose_name='Approved go live at', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='pagerevision',
            name='content_json',
            field=models.TextField(verbose_name='Content JSON'),
        ),
        migrations.AlterField(
            model_name='pagerevision',
            name='created_at',
            field=models.DateTimeField(verbose_name='Created at'),
        ),
        migrations.AlterField(
            model_name='pagerevision',
            name='page',
            field=models.ForeignKey(related_name='revisions', to='wagtailcore.Page', verbose_name='Page'),
        ),
        migrations.AlterField(
            model_name='pagerevision',
            name='submitted_for_moderation',
            field=models.BooleanField(verbose_name='Submitted for moderation', default=False),
        ),
        migrations.AlterField(
            model_name='pagerevision',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, verbose_name='User', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='page',
            name='url_path',
            field=models.TextField(verbose_name='URL path', editable=False, blank=True),
        ),
    ]
