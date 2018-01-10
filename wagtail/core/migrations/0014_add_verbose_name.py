# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0013_update_golive_expire_help_text'),
    ]

    operations = [
        migrations.AlterField(
            model_name='grouppagepermission',
            name='group',
            field=models.ForeignKey(on_delete=models.CASCADE, verbose_name='Group', related_name='page_permissions', to='auth.Group'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='grouppagepermission',
            name='page',
            field=models.ForeignKey(on_delete=models.CASCADE, verbose_name='Page', related_name='group_permissions', to='wagtailcore.Page'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='grouppagepermission',
            name='permission_type',
            field=models.CharField(
                choices=[
                    ('add', 'Add/edit pages you own'),
                    ('edit', 'Add/edit any page'),
                    ('publish', 'Publish any page'),
                    ('lock', 'Lock/unlock any page')
                ],
                max_length=20,
                verbose_name='Permission type'
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='page',
            name='search_description',
            field=models.TextField(blank=True, verbose_name='Search description'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='page',
            name='show_in_menus',
            field=models.BooleanField(
                default=False,
                help_text='Whether a link to this page will appear in automatically generated menus',
                verbose_name='Show in menus'
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='page',
            name='slug',
            field=models.SlugField(
                help_text='The name of the page as it will appear in URLs e.g http://domain.com/blog/[my-slug]/',
                max_length=255,
                verbose_name='Slug'
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='page',
            name='title',
            field=models.CharField(
                help_text="The page title as you'd like it to be seen by the public",
                max_length=255,
                verbose_name='Title'
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='pageviewrestriction',
            name='page',
            field=models.ForeignKey(on_delete=models.CASCADE, verbose_name='Page', related_name='view_restrictions', to='wagtailcore.Page'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='pageviewrestriction',
            name='password',
            field=models.CharField(max_length=255, verbose_name='Password'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='site',
            name='hostname',
            field=models.CharField(db_index=True, max_length=255, verbose_name='Hostname'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='site',
            name='is_default_site',
            field=models.BooleanField(
                default=False,
                help_text='If true, this site will handle requests for all other hostnames'
                ' that do not have a site entry of their own',
                verbose_name='Is default site'
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='site',
            name='port',
            field=models.IntegerField(
                default=80,
                help_text='Set this to something other than 80 if you need a specific port number'
                ' to appear in URLs (e.g. development on port 8000). Does not affect request handling'
                ' (so port forwarding still works).',
                verbose_name='Port'
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='site',
            name='root_page',
            field=models.ForeignKey(on_delete=models.CASCADE, verbose_name='Root page', related_name='sites_rooted_here', to='wagtailcore.Page'),
            preserve_default=True,
        ),
    ]
