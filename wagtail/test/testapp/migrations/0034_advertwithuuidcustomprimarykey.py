# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ('tests', '0033_eventpagespeaker_related_query_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdvertWithCustomUUIDPrimaryKey',
            fields=[
                ('advert_id', models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4, serialize=False)),
                ('url', models.URLField(blank=True, null=True)),
                ('text', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
