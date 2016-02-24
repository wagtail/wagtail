# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import wagtail.wagtailimages.models
import taggit.managers
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0008_image_created_at_index'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='created at'),
        ),
        migrations.AlterField(
            model_name='image',
            name='file',
            field=models.ImageField(upload_to=wagtail.wagtailimages.models.get_upload_to, height_field='height', width_field='width', verbose_name='file'),
        ),
        migrations.AlterField(
            model_name='image',
            name='height',
            field=models.IntegerField(editable=False, verbose_name='height'),
        ),
        migrations.AlterField(
            model_name='image',
            name='tags',
            field=taggit.managers.TaggableManager(through='taggit.TaggedItem', verbose_name='tags', blank=True, help_text=None, to='taggit.Tag'),
        ),
        migrations.AlterField(
            model_name='image',
            name='title',
            field=models.CharField(max_length=255, verbose_name='title'),
        ),
        migrations.AlterField(
            model_name='image',
            name='uploaded_by_user',
            field=models.ForeignKey(on_delete=models.CASCADE, blank=True, null=True, to=settings.AUTH_USER_MODEL, editable=False, verbose_name='uploaded by user'),
        ),
        migrations.AlterField(
            model_name='image',
            name='width',
            field=models.IntegerField(editable=False, verbose_name='width'),
        ),
    ]
