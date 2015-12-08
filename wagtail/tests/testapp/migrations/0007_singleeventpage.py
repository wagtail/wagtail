# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0006_image_file_size'),
    ]

    operations = [
        migrations.CreateModel(
            name='SingleEventPage',
            fields=[
                (
                    'eventpage_ptr',
                    models.OneToOneField(
                        auto_created=True,
                        to='tests.EventPage',
                        serialize=False,
                        parent_link=True,
                        primary_key=True
                    )
                ),
                (
                    'excerpt',
                    models.TextField(
                        help_text='Short text to describe what is this action about',
                        max_length=255,
                        null=True,
                        blank=True
                    )
                ),
            ],
            bases=('tests.eventpage',),
        ),
    ]
