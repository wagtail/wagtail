# -*- coding: utf-8 -*-
# Generated by Django 1.10a1 on 2016-06-16 08:30
from __future__ import unicode_literals

from django.db import migrations
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0029_unicode_slugfield_dj19'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='collection',
            managers=[
                ('objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='page',
            managers=[
                ('objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='pagerevision',
            managers=[
                ('objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='site',
            managers=[
                ('objects', django.db.models.manager.Manager()),
            ],
        ),
    ]
