# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0022_add_site_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pagerevision',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                verbose_name='user', blank=True, to=settings.AUTH_USER_MODEL, null=True
            ),
        ),
    ]
