# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0003_add_uniqueness_constraint_on_group_page_permission'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='locked',
            field=models.BooleanField(default=False, editable=False),
            preserve_default=True,
        ),
    ]
