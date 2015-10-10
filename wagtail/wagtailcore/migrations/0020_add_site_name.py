# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0019_verbose_names_cleanup'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='site_name',
            field=models.CharField(db_index=True, verbose_name='Site name', null=True, blank=True, max_length=255, help_text="Human-readable name for the site."),
        ),
    ]
