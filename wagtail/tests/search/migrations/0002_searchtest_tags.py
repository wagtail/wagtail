# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0001_initial'),
        ('searchtests', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='searchtest',
            name='tags',
            field=taggit.managers.TaggableManager(through='taggit.TaggedItem', verbose_name='Tags', to='taggit.Tag', help_text='A comma-separated list of tags.'),
        ),
    ]
