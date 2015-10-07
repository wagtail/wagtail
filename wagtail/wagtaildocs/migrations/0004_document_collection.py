# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import wagtail.wagtailcore.models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0021_collection_initial_data'),
        ('wagtaildocs', '0003_add_verbose_names'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='collection',
            field=models.ForeignKey(related_name='+', to='wagtailcore.Collection', verbose_name='collection', default=wagtail.wagtailcore.models.get_root_collection_id),
            preserve_default=True,
        ),
    ]
