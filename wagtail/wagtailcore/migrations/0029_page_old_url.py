# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0028_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='old_url',
            field=models.TextField(null=True, help_text='Will be null if page url has not changed after a save. Otherwise will be the previous page url.', editable=False, verbose_name='old page url', blank=True),
        ),
    ]
