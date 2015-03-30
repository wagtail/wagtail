# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0003_auto_20140905_0634'),
    ]

    operations = [
        migrations.DeleteModel(
            name='SearchTestOldConfig',
        ),
        migrations.DeleteModel(
            name='SearchTestOldConfigList',
        ),
    ]
