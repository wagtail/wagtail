# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0013_auto_20150330_0717'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='searchtestchild',
            name='searchtest_ptr',
        ),
        migrations.DeleteModel(
            name='SearchTestChild',
        ),
        migrations.DeleteModel(
            name='SearchTest',
        ),
    ]
