# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import taggit.managers
from django.conf import settings
from django.db import migrations, models

import wagtail.wagtailadmin.taggable


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '__latest__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Title')),
                ('file', models.FileField(upload_to='documents', verbose_name='File')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'tags',
                    taggit.managers.TaggableManager(
                        to='taggit.Tag',
                        verbose_name='Tags',
                        help_text=None,
                        blank=True,
                        through='taggit.TaggedItem'
                    )
                ),
                (
                    'uploaded_by_user',
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        editable=False,
                        null=True,
                        blank=True,
                        to=settings.AUTH_USER_MODEL
                    )
                ),
            ],
            options={
            },
            bases=(models.Model, wagtail.wagtailadmin.taggable.TagSearchable),
        ),
    ]
