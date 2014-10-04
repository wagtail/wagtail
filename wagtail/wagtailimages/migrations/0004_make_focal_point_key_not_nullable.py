# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0003_fix_focal_point_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rendition',
            name='focal_point_key',
            field=models.CharField(blank=True, default='', max_length=255, editable=False),
        ),
    ]
