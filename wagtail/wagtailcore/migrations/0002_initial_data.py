# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from wagtail.wagtailcore.migration_tools.initial_data import create_initial_data, remove_initial_data


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_data, remove_initial_data),
    ]
