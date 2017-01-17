# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0016_deprecate_rendition_filter_relation'),
    ]

    operations = [
        # The Wagtail 1.8 version of migration wagtailimages/0016 did not include the
        # step to reduce focal_point_key's max_length to 16, necessary to make it work
        # on some MySQL configurations. This migration serves only to ensure that
        # installations upgrading from 1.8 to >=1.8.1 have this change applied; on other
        # setups (where the current 0016 and 0017 are applied together), this is a no-op.
        migrations.AlterField(
            model_name='rendition',
            name='focal_point_key',
            field=models.CharField(blank=True, default='', max_length=16, editable=False),
        ),
    ]
