# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    """
    When the initial migration was created, the focal point fields on image
    did not have blank=True set.

    This migration fixes this.
    """

    dependencies = [
        ('wagtailimages', '0002_initial_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='focal_point_height',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='image',
            name='focal_point_width',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='image',
            name='focal_point_x',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='image',
            name='focal_point_y',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
    ]
