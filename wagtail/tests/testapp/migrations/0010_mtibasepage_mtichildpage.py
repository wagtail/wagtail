# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0019_verbose_names_cleanup'),
        ('tests', '0009_auto_20150820_0419'),
    ]

    operations = [
        migrations.CreateModel(
            name='MTIBasePage',
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
        migrations.CreateModel(
            name='MTIChildPage',
            fields=[
                (
                    'mtibasepage_ptr',
                    models.OneToOneField(
                        parent_link=True,
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        to='tests.MTIBasePage'
                    )
                ),
            ],
            options={
                'abstract': False,
            },
            bases=('tests.mtibasepage',),
        ),
    ]
