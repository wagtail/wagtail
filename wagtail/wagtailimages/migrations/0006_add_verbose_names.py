# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0005_make_filter_spec_unique'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created at'),
        ),
        migrations.AlterField(
            model_name='image',
            name='height',
            field=models.IntegerField(verbose_name='Height', editable=False),
        ),
        migrations.AlterField(
            model_name='image',
            name='uploaded_by_user',
            field=models.ForeignKey(
                blank=True, editable=False, to=settings.AUTH_USER_MODEL, null=True,
                verbose_name='Uploaded by user'
            ),
        ),
        migrations.AlterField(
            model_name='image',
            name='width',
            field=models.IntegerField(verbose_name='Width', editable=False),
        ),
    ]
