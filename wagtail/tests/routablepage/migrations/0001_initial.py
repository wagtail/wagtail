# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import wagtail.contrib.wagtailroutablepage.models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0013_update_golive_expire_help_text'),
    ]

    operations = [
        migrations.CreateModel(
            name='RoutablePageTest',
            fields=[
                ('page_ptr', models.OneToOneField(to='wagtailcore.Page', serialize=False, auto_created=True, primary_key=True, parent_link=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(wagtail.contrib.wagtailroutablepage.models.RoutablePageMixin, 'wagtailcore.page'),
        ),
    ]
