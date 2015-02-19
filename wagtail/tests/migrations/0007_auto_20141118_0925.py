# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0006_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pagechoosermodel',
            name='page',
            field=models.ForeignKey(to='wagtailcore.Page', help_text='help text'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='snippetchoosermodel',
            name='advert',
            field=models.ForeignKey(to='tests.Advert', help_text='help text'),
            preserve_default=True,
        ),
    ]
