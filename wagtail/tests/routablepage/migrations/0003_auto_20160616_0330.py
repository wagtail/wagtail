# -*- coding: utf-8 -*-
# Generated by Django 1.10a1 on 2016-06-16 08:30
from __future__ import unicode_literals

from django.db import migrations
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('routablepagetests', '0002_routablepagewithoutindexroutetest'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='routablepagetest',
            managers=[
                ('objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='routablepagewithoutindexroutetest',
            managers=[
                ('objects', django.db.models.manager.Manager()),
            ],
        ),
    ]
