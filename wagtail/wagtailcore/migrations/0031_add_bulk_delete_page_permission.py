# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-27 14:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0030_index_on_pagerevision_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='grouppagepermission',
            name='permission_type',
            field=models.CharField(choices=[('add', 'Add/edit pages you own'), ('edit', 'Edit any page'), ('publish', 'Publish any page'), ('bulk_delete', 'Delete pages with children'), ('lock', 'Lock/unlock any page')], max_length=20, verbose_name='permission type'),
        ),
    ]
