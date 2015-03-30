# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0011_auto_20150330_0653'),
    ]

    operations = [
        migrations.DeleteModel(
            name='AlphaSnippet',
        ),
        migrations.DeleteModel(
            name='RegisterDecorator',
        ),
        migrations.DeleteModel(
            name='RegisterFunction',
        ),
        migrations.DeleteModel(
            name='ZuluSnippet',
        ),
    ]
