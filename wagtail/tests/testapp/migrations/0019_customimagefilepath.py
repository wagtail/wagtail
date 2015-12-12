# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import taggit.managers
import wagtail.wagtailadmin.taggable
import wagtail.wagtailimages.models


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tests', '0018_singletonpage'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomImageFilePath',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, verbose_name='Title')),
                ('file', models.ImageField(height_field='height', upload_to=wagtail.wagtailimages.models.get_upload_to, width_field='width', verbose_name='File')),
                ('width', models.IntegerField(verbose_name='Width', editable=False)),
                ('height', models.IntegerField(verbose_name='Height', editable=False)),
                ('created_at', models.DateTimeField(db_index=True, auto_now_add=True, verbose_name='Created at')),
                ('focal_point_x', models.PositiveIntegerField(null=True, blank=True)),
                ('focal_point_y', models.PositiveIntegerField(null=True, blank=True)),
                ('focal_point_width', models.PositiveIntegerField(null=True, blank=True)),
                ('focal_point_height', models.PositiveIntegerField(null=True, blank=True)),
                ('tags', taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', blank=True, help_text=None, verbose_name='Tags')),
                ('uploaded_by_user', models.ForeignKey(blank=True, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Uploaded by user')),
                ('file_size', models.PositiveIntegerField(null=True, editable=False)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, wagtail.wagtailadmin.taggable.TagSearchable),
        ),
    ]
