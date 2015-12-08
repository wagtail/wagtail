# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailredirects', '0002_add_verbose_names'),
    ]

    operations = [
        migrations.AlterField(
            model_name='redirect',
            name='site',
            field=models.ForeignKey(
                null=True, to='wagtailcore.Site', verbose_name='Site', blank=True, related_name='redirects'
            ),
        ),
    ]
