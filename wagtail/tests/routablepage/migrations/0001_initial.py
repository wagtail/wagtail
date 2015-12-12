# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import wagtail.contrib.wagtailroutablepage.models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0019_verbose_names_cleanup'),
    ]

    operations = [
        migrations.CreateModel(
            name='RoutablePageTest',
            fields=[
                (
                    'page_ptr',
                    models.OneToOneField(
                        parent_link=True, auto_created=True, serialize=False, to='wagtailcore.Page', primary_key=True
                    )
                ),
            ],
            options={
                'abstract': False,
            },
            bases=(wagtail.contrib.wagtailroutablepage.models.RoutablePageMixin, 'wagtailcore.page'),
        ),
    ]
