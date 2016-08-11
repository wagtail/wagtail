# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0014_add_verbose_name'),
    ]

    operations = [
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
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='pages', verbose_name='Content type', to='contenttypes.ContentType'),
        ),
        migrations.AlterField(
            model_name='page',
            name='expired',
            field=models.BooleanField(default=False, verbose_name='Expired', editable=False),
        ),
        migrations.AlterField(
            model_name='page',
            name='first_published_at',
            field=models.DateTimeField(verbose_name='First published at', null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='page',
            name='has_unpublished_changes',
            field=models.BooleanField(default=False, verbose_name='Has unpublished changes', editable=False),
        ),
        migrations.AlterField(
            model_name='page',
            name='latest_revision_created_at',
            field=models.DateTimeField(verbose_name='Latest revision created at', null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='page',
            name='live',
            field=models.BooleanField(default=True, verbose_name='Live', editable=False),
        ),
        migrations.AlterField(
            model_name='page',
            name='locked',
            field=models.BooleanField(default=False, verbose_name='Locked', editable=False),
        ),
        migrations.AlterField(
            model_name='page',
            name='owner',
            field=models.ForeignKey(
                related_name='owned_pages',
                on_delete=django.db.models.deletion.SET_NULL,
                blank=True,
                editable=False,
                to=settings.AUTH_USER_MODEL,
                null=True,
                verbose_name='Owner'
            ),
        ),
        migrations.AlterField(
            model_name='page',
            name='url_path',
            field=models.CharField(verbose_name='URL path', max_length=255, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='pagerevision',
            name='approved_go_live_at',
            field=models.DateTimeField(null=True, verbose_name='Approved go live at', blank=True),
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
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='revisions', verbose_name='Page', to='wagtailcore.Page'),
        ),
        migrations.AlterField(
            model_name='pagerevision',
            name='submitted_for_moderation',
            field=models.BooleanField(default=False, verbose_name='Submitted for moderation'),
        ),
        migrations.AlterField(
            model_name='pagerevision',
            name='user',
            field=models.ForeignKey(on_delete=models.CASCADE, verbose_name='User', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
