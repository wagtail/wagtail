# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailembeds', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='embed',
            options={'verbose_name': 'Embed'},
        ),
    ]
