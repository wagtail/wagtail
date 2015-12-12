# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0019_verbose_names_cleanup'),
        ('tests', '0011_auto_20151006_2141'),
    ]

    operations = [
        migrations.CreateModel(
            name='FilePage',
            fields=[
                (
                    'page_ptr',
                    models.OneToOneField(
                        to='wagtailcore.Page',
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                        parent_link=True
                    )
                ),
                ('file_field', models.FileField(upload_to='')),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
    ]
