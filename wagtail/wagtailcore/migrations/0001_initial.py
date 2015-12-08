# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import wagtail.wagtailsearch.index


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupPagePermission',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                (
                    'permission_type',
                    models.CharField(choices=[('add', 'Add'), ('edit', 'Edit'), ('publish', 'Publish')], max_length=20)
                ),
                ('group', models.ForeignKey(to='auth.Group', related_name='page_permissions')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('path', models.CharField(max_length=255, unique=True)),
                ('depth', models.PositiveIntegerField()),
                ('numchild', models.PositiveIntegerField(default=0)),
                ('title', models.CharField(
                    max_length=255,
                    help_text="The page title as you'd like it to be seen by the public"
                )),
                ('slug', models.SlugField(
                    help_text='The name of the page as it will appear in URLs e.g http://domain.com/blog/[my-slug]/'
                )),
                ('live', models.BooleanField(default=True, editable=False)),
                ('has_unpublished_changes', models.BooleanField(default=False, editable=False)),
                ('url_path', models.CharField(blank=True, max_length=255, editable=False)),
                ('seo_title', models.CharField(
                    blank=True,
                    max_length=255,
                    help_text=(
                        "Optional. 'Search Engine Friendly' title."
                        " This will appear at the top of the browser window."
                    ),
                    verbose_name='Page title'
                )),
                ('show_in_menus', models.BooleanField(
                    default=False,
                    help_text='Whether a link to this page will appear in automatically generated menus'
                )),
                ('search_description', models.TextField(blank=True)),
                ('go_live_at', models.DateTimeField(
                    blank=True,
                    verbose_name='Go live date/time',
                    null=True, help_text='Please add a date-time in the form YYYY-MM-DD hh:mm:ss.'
                )),
                ('expire_at', models.DateTimeField(
                    blank=True,
                    verbose_name='Expiry date/time',
                    null=True,
                    help_text='Please add a date-time in the form YYYY-MM-DD hh:mm:ss.'
                )),
                ('expired', models.BooleanField(default=False, editable=False)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', related_name='pages')),
                ('owner', models.ForeignKey(
                    blank=True, null=True, to=settings.AUTH_USER_MODEL, editable=False, related_name='owned_pages'
                )),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, wagtail.wagtailsearch.index.Indexed),
        ),
        migrations.CreateModel(
            name='PageRevision',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('submitted_for_moderation', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('content_json', models.TextField()),
                ('approved_go_live_at', models.DateTimeField(blank=True, null=True)),
                ('page', models.ForeignKey(to='wagtailcore.Page', related_name='revisions')),
                ('user', models.ForeignKey(blank=True, null=True, to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PageViewRestriction',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('password', models.CharField(max_length=255)),
                ('page', models.ForeignKey(to='wagtailcore.Page', related_name='view_restrictions')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Site',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('hostname', models.CharField(max_length=255, db_index=True)),
                ('port', models.IntegerField(
                    default=80,
                    help_text=(
                        'Set this to something other than 80 if you need a specific port number'
                        ' to appear in URLs (e.g. development on port 8000).'
                        ' Does not affect request handling (so port forwarding still works).'
                    )
                )),
                ('is_default_site', models.BooleanField(
                    default=False,
                    help_text=(
                        'If true, this site will handle requests for all other hostnames'
                        ' that do not have a site entry of their own'
                    )
                )),
                ('root_page', models.ForeignKey(to='wagtailcore.Page', related_name='sites_rooted_here')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='site',
            unique_together=set([('hostname', 'port')]),
        ),
        migrations.AddField(
            model_name='grouppagepermission',
            name='page',
            field=models.ForeignKey(to='wagtailcore.Page', related_name='group_permissions'),
            preserve_default=True,
        ),
    ]
