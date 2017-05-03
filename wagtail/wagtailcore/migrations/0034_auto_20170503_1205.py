# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-05-03 12:05
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0033_remove_golive_expiry_help_text'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='owned_pages', to=settings.AUTH_USER_MODEL, verbose_name='owner'),
        ),
    ]
