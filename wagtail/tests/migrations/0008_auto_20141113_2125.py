# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0007_registerdecorator'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pagechoosermodel',
            name='page',
            field=models.ForeignKey(help_text='help text', to='wagtailcore.Page'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='snippetchoosermodel',
            name='advert',
            field=models.ForeignKey(help_text='help text', to='tests.Advert'),
            preserve_default=True,
        ),
    ]
