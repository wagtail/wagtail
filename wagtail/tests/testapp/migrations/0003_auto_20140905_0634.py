# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0002_auto_20140827_0908'),
    ]

    operations = [
        migrations.AddField(
            model_name='advertplacement',
            name='colour',
            field=models.CharField(default='blue', max_length=255),
            preserve_default=False,
        ),
    ]
