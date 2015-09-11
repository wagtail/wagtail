# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0006_image_file_size'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customimagewithadminformfields',
            name='created_at',
            field=models.DateTimeField(db_index=True, verbose_name='Created at', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='customimagewithoutadminformfields',
            name='created_at',
            field=models.DateTimeField(db_index=True, verbose_name='Created at', auto_now_add=True),
        ),
    ]
