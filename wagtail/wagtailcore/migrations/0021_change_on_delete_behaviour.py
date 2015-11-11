# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0020_add_index_on_page_first_published_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='owner',
            field=models.ForeignKey(related_name='owned_pages', on_delete=django.db.models.deletion.SET_NULL, verbose_name='Owner', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='pagerevision',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='User', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
