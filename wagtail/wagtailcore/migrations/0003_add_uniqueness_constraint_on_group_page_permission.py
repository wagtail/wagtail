# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0002_initial_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='grouppagepermission',
            name='permission_type',
            field=models.CharField(
                max_length=20,
                choices=[
                    (b'add', b'Add/edit pages you own'),
                    (b'edit', b'Add/edit any page'),
                    (b'publish', b'Publish any page')
                ]
            ),
        ),
        migrations.AlterUniqueTogether(
            name='grouppagepermission',
            unique_together=set([('group', 'page', 'permission_type')]),
        ),
    ]
