# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0015_add_more_verbose_names'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='url_path',
            field=models.TextField(verbose_name='URL path', editable=False, blank=True),
            preserve_default=True,
        ),
    ]
