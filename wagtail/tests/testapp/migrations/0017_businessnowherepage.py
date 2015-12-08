# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0020_add_index_on_page_first_published_at'),
        ('tests', '0016_mtibasepage_verbose_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusinessNowherePage',
            fields=[
                (
                    'page_ptr',
                    models.OneToOneField(
                        serialize=False,
                        auto_created=True,
                        to='wagtailcore.Page',
                        primary_key=True,
                        parent_link=True
                    )
                ),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
    ]
