# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0005_streampage'),
    ]

    operations = [
        migrations.AddField(
            model_name='customimagewithadminformfields',
            name='file_size',
            field=models.PositiveIntegerField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name='customimagewithoutadminformfields',
            name='file_size',
            field=models.PositiveIntegerField(null=True, editable=False),
        ),
    ]
