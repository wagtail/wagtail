# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0001_squashed_0016_change_page_url_path_to_text_field'),
        ('searchtests', '0002_searchtest_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='searchtestchild',
            name='page',
            field=models.ForeignKey(to='wagtailcore.Page', blank=True, null=True),
        ),
    ]
