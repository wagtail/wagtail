# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0008_populate_latest_revision_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pagerevision',
            name='created_at',
            field=models.DateTimeField(),
        ),
    ]
