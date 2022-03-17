# -*- coding: utf-8 -*-
from django.db import migrations, models

import wagtail.models


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0026_group_collection_permission"),
        ("wagtailimages", "0010_change_on_delete_behaviour"),
    ]

    operations = [
        migrations.AddField(
            model_name="image",
            name="collection",
            field=models.ForeignKey(
                to="wagtailcore.Collection",
                verbose_name="collection",
                default=wagtail.models.get_root_collection_id,
                related_name="+",
                on_delete=models.CASCADE,
            ),
        ),
    ]
