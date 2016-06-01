# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0028_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pagerevision',
            name='created_at',
            field=models.DateTimeField(db_index=True, verbose_name='created at'),
        ),
    ]
