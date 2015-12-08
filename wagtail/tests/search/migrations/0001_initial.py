# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import wagtail.wagtailsearch.index


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SearchTest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('content', models.TextField()),
                ('live', models.BooleanField(default=False)),
                ('published_date', models.DateField(null=True)),
            ],
            options={
            },
            bases=(models.Model, wagtail.wagtailsearch.index.Indexed),
        ),
        migrations.CreateModel(
            name='SearchTestChild',
            fields=[
                (
                    'searchtest_ptr',
                    models.OneToOneField(
                        primary_key=True,
                        serialize=False,
                        parent_link=True,
                        to='searchtests.SearchTest',
                        auto_created=True
                    )
                ),
                ('subtitle', models.CharField(null=True, max_length=255, blank=True)),
                ('extra_content', models.TextField()),
            ],
            options={
            },
            bases=('searchtests.searchtest',),
        ),
    ]
