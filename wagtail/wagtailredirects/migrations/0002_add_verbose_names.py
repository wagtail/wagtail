# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailredirects', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='redirect',
            options={'verbose_name': 'Redirect'},
        ),
        migrations.AlterField(
            model_name='redirect',
            name='site',
            field=models.ForeignKey(
                related_name='redirects', blank=True, editable=False,
                to='wagtailcore.Site', null=True, verbose_name='Site'
            ),
        ),
    ]
