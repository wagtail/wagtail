# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0020_add_index_on_page_first_published_at'),
        ('tests', '0017_businessnowherepage'),
    ]

    operations = [
        migrations.CreateModel(
            name='SingletonPage',
            fields=[
                (
                    'page_ptr',
                    models.OneToOneField(
                        parent_link=True,
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        to='wagtailcore.Page'
                    )
                ),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
    ]
