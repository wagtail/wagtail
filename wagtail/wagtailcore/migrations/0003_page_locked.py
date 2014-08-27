# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0002_initial_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='locked',
            field=models.BooleanField(editable=False, default=False),
            preserve_default=True,
        ),
    ]
