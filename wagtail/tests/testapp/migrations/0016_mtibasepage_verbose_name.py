# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0015_genericsnippetpage'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='mtibasepage',
            options={'verbose_name': 'MTI Base page'},
        ),
    ]
