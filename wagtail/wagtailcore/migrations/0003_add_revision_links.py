# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0002_initial_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='first_revision',
            field=models.ForeignKey(related_name='+', editable=False, on_delete=django.db.models.deletion.SET_NULL, to='wagtailcore.PageRevision', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='page',
            name='last_revision',
            field=models.ForeignKey(related_name='+', editable=False, on_delete=django.db.models.deletion.SET_NULL, to='wagtailcore.PageRevision', null=True),
            preserve_default=True,
        ),
    ]
