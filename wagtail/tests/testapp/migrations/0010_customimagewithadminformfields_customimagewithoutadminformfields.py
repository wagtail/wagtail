# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import wagtail.wagtailadmin.taggable
from django.conf import settings
import taggit.managers
import wagtail.wagtailimages.models


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0001_initial'),
        ('tests', '0009_eventpagechoosermodel'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomImageWithAdminFormFields',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('title', models.CharField(verbose_name='Title', max_length=255)),
                ('file', models.ImageField(verbose_name='File', height_field='height', upload_to=wagtail.wagtailimages.models.get_upload_to, width_field='width')),
                ('width', models.IntegerField(editable=False)),
                ('height', models.IntegerField(editable=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('focal_point_x', models.PositiveIntegerField(blank=True, null=True)),
                ('focal_point_y', models.PositiveIntegerField(blank=True, null=True)),
                ('focal_point_width', models.PositiveIntegerField(blank=True, null=True)),
                ('focal_point_height', models.PositiveIntegerField(blank=True, null=True)),
                ('caption', models.CharField(max_length=255)),
                ('not_editable_field', models.CharField(max_length=255)),
                ('tags', taggit.managers.TaggableManager(verbose_name='Tags', help_text=None, through='taggit.TaggedItem', blank=True, to='taggit.Tag')),
                ('uploaded_by_user', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, blank=True, editable=False)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, wagtail.wagtailadmin.taggable.TagSearchable),
        ),
        migrations.CreateModel(
            name='CustomImageWithoutAdminFormFields',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('title', models.CharField(verbose_name='Title', max_length=255)),
                ('file', models.ImageField(verbose_name='File', height_field='height', upload_to=wagtail.wagtailimages.models.get_upload_to, width_field='width')),
                ('width', models.IntegerField(editable=False)),
                ('height', models.IntegerField(editable=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('focal_point_x', models.PositiveIntegerField(blank=True, null=True)),
                ('focal_point_y', models.PositiveIntegerField(blank=True, null=True)),
                ('focal_point_width', models.PositiveIntegerField(blank=True, null=True)),
                ('focal_point_height', models.PositiveIntegerField(blank=True, null=True)),
                ('caption', models.CharField(max_length=255)),
                ('not_editable_field', models.CharField(max_length=255)),
                ('tags', taggit.managers.TaggableManager(verbose_name='Tags', help_text=None, through='taggit.TaggedItem', blank=True, to='taggit.Tag')),
                ('uploaded_by_user', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, blank=True, editable=False)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, wagtail.wagtailadmin.taggable.TagSearchable),
        ),
    ]
