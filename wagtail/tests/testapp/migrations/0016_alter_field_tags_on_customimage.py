# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0015_genericsnippetpage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customimage',
            name='tags',
            field=taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', blank=True, help_text='Multi-word tags should be enclosed in quotes, otherwise they would appear as separate tags.', verbose_name='Tags'),
        ),
    ]
