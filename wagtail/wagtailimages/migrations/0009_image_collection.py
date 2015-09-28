# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import wagtail.wagtailcore.models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0022_group_collection_permission'),
        ('wagtailimages', '0008_image_created_at_index'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='collection',
            field=models.ForeignKey(to='wagtailcore.Collection', verbose_name='collection', default=wagtail.wagtailcore.models.get_root_collection_id, related_name='+'),
        ),
    ]
