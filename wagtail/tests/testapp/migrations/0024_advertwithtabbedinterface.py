# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0023_mycustompage'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdvertWithTabbedInterface',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(null=True, blank=True)),
                ('text', models.CharField(max_length=255)),
                ('something_else', models.CharField(max_length=255)),
            ],
        ),
    ]
