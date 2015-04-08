# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import wagtail.contrib.wagtailroutablepage.models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0013_update_golive_expire_help_text'),
        ('routablepagetests', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OldStyleRoutablePageTest',
            fields=[
                ('page_ptr', models.OneToOneField(primary_key=True, auto_created=True, serialize=False, to='wagtailcore.Page', parent_link=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(wagtail.contrib.wagtailroutablepage.models.RoutablePageMixin, 'wagtailcore.page'),
        ),
        migrations.RenameModel(
            old_name='RoutablePageTest',
            new_name='NewStyleRoutablePageTest',
        ),
    ]
