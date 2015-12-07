# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0008_image_created_at_index'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='tags',
            field=taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', blank=True, help_text='Multi-word tags should be enclosed in quotes, otherwise they would appear as separate tags.', verbose_name='Tags'),
        ),
    ]
