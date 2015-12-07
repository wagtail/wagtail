# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import taggit.managers
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0001_initial'),
        ('tests', '0008_merge'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdvertTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content_object', modelcluster.fields.ParentalKey(related_name='tagged_items', to='tests.Advert')),
                ('tag', models.ForeignKey(related_name='tests_adverttag_items', to='taggit.Tag')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='advert',
            name='tags',
            field=taggit.managers.TaggableManager(
                to='taggit.Tag',
                through='tests.AdvertTag',
                blank=True,
                help_text='A comma-separated list of tags.',
                verbose_name='Tags'
            ),
        ),
    ]
