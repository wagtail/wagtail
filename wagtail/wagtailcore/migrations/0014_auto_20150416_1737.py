# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0013_update_golive_expire_help_text'),
    ]

    operations = [
        migrations.AlterField(
            model_name='grouppagepermission',
            name='group',
            field=models.ForeignKey(related_name='page_permissions', verbose_name='group', to='auth.Group'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='grouppagepermission',
            name='page',
            field=models.ForeignKey(related_name='group_permissions', verbose_name='page', to='wagtailcore.Page'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='grouppagepermission',
            name='permission_type',
            field=models.CharField(max_length=20, verbose_name='permission type', choices=[('add', 'Add/edit pages you own'), ('edit', 'Add/edit any page'), ('publish', 'Publish any page'), ('lock', 'Lock/unlock any page')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='page',
            name='search_description',
            field=models.TextField(verbose_name='search description', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='page',
            name='seo_title',
            field=models.CharField(help_text="Optional. 'Search Engine Friendly' title. This will appear at the top of the browser window.", max_length=255, verbose_name='page title', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='page',
            name='show_in_menus',
            field=models.BooleanField(default=False, help_text='Whether a link to this page will appear in automatically generated menus', verbose_name='show in menus'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='page',
            name='slug',
            field=models.SlugField(help_text='The name of the page as it will appear in URLs e.g http://domain.com/blog/[my-slug]/', max_length=255, verbose_name='slug'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='page',
            name='title',
            field=models.CharField(help_text="The page title as you'd like it to be seen by the public", max_length=255, verbose_name='title'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='pageviewrestriction',
            name='page',
            field=models.ForeignKey(related_name='view_restrictions', verbose_name='page', to='wagtailcore.Page'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='pageviewrestriction',
            name='password',
            field=models.CharField(max_length=255, verbose_name='password'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='site',
            name='hostname',
            field=models.CharField(max_length=255, verbose_name='hostname', db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='site',
            name='is_default_site',
            field=models.BooleanField(default=False, help_text='If true, this site will handle requests for all other hostnames that do not have a site entry of their own', verbose_name='is default site'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='site',
            name='port',
            field=models.IntegerField(default=80, help_text='Set this to something other than 80 if you need a specific port number to appear in URLs (e.g. development on port 8000). Does not affect request handling (so port forwarding still works).', verbose_name='port'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='site',
            name='root_page',
            field=models.ForeignKey(related_name='sites_rooted_here', verbose_name='root page', to='wagtailcore.Page'),
            preserve_default=True,
        ),
    ]
