# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0019_verbose_names_cleanup'),
    ]

    operations = [
        migrations.AlterField(
            model_name='grouppagepermission',
            name='permission_type',
            field=models.CharField(max_length=20, verbose_name='Permission type', choices=[('add', 'Add/edit pages you own'), ('edit', 'Edit any page'), ('share', 'Share any page'), ('publish', 'Publish any page'), ('lock', 'Lock/unlock any page')]),
        ),
    ]
