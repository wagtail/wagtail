# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0017_change_edit_page_permission_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pagerevision',
            name='submitted_for_moderation',
            field=models.BooleanField(default=False, db_index=True, verbose_name='Submitted for moderation'),
        ),
    ]
