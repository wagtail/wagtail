# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailembeds', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='embed',
            name='author_name',
            field=models.TextField(default='', blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='embed',
            name='provider_name',
            field=models.TextField(default='', blank=True),
            preserve_default=False,
        ),
    ]
