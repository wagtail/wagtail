# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0005_add_page_lock_permission_to_moderators'),
    ]

    operations = [
        migrations.AlterField(
            model_name='grouppagepermission',
            name='permission_type',
            field=models.CharField(max_length=20, choices=[(b'add', b'Add/edit pages you own'), (b'edit', b'Add/edit any page'), (b'publish', b'Publish any page'), (b'lock', b'Lock/unlock any page')]),
        ),
    ]
