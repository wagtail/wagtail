# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import wagtail.wagtailsearch.indexed


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupPagePermission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('permission_type', models.CharField(max_length=20, choices=[(b'add', b'Add'), (b'edit', b'Edit'), (b'publish', b'Publish')])),
                ('group', models.ForeignKey(to='auth.Group')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('path', models.CharField(unique=True, max_length=255)),
                ('depth', models.PositiveIntegerField()),
                ('numchild', models.PositiveIntegerField(default=0)),
                ('title', models.CharField(help_text="The page title as you'd like it to be seen by the public", max_length=255)),
                ('slug', models.SlugField(help_text='The name of the page as it will appear in URLs e.g http://domain.com/blog/[my-slug]/')),
                ('live', models.BooleanField(default=True, editable=False)),
                ('has_unpublished_changes', models.BooleanField(default=False, editable=False)),
                ('url_path', models.CharField(max_length=255, editable=False, blank=True)),
                ('seo_title', models.CharField(help_text="Optional. 'Search Engine Friendly' title. This will appear at the top of the browser window.", max_length=255, verbose_name='Page title', blank=True)),
                ('show_in_menus', models.BooleanField(default=False, help_text='Whether a link to this page will appear in automatically generated menus')),
                ('search_description', models.TextField(blank=True)),
                ('go_live_at', models.DateTimeField(help_text='Please add a date-time in the form YYYY-MM-DD hh:mm.', null=True, verbose_name='Go live date/time', blank=True)),
                ('expire_at', models.DateTimeField(help_text='Please add a date-time in the form YYYY-MM-DD hh:mm.', null=True, verbose_name='Expiry date/time', blank=True)),
                ('expired', models.BooleanField(default=False, editable=False)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('owner', models.ForeignKey(blank=True, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, wagtail.wagtailsearch.indexed.Indexed),
        ),
        migrations.AddField(
            model_name='grouppagepermission',
            name='page',
            field=models.ForeignKey(to='wagtailcore.Page'),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='PageRevision',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('submitted_for_moderation', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('content_json', models.TextField()),
                ('approved_go_live_at', models.DateTimeField(null=True, blank=True)),
                ('page', models.ForeignKey(to='wagtailcore.Page')),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PageViewRestriction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=255)),
                ('page', models.ForeignKey(to='wagtailcore.Page')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Site',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('hostname', models.CharField(max_length=255, db_index=True)),
                ('port', models.IntegerField(default=80, help_text='Set this to something other than 80 if you need a specific port number to appear in URLs (e.g. development on port 8000). Does not affect request handling (so port forwarding still works).')),
                ('is_default_site', models.BooleanField(default=False, help_text='If true, this site will handle requests for all other hostnames that do not have a site entry of their own')),
                ('root_page', models.ForeignKey(to='wagtailcore.Page')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='site',
            unique_together=set([(b'hostname', b'port')]),
        ),
    ]
