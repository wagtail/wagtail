# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('wagtailcore', '0010_change_page_owner_to_null_on_delete'),
    ]

    operations = [
        migrations.AddField(
            model_name='pageviewrestriction',
            name='groups',
            field=models.ManyToManyField(to='auth.Group'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='pageviewrestriction',
            name='password',
            field=models.CharField(max_length=255, blank=True),
            preserve_default=True,
        ),
    ]
