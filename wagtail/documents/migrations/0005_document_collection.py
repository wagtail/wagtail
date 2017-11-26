# -*- coding: utf-8 -*-
from django.db import migrations, models

import wagtail.core.models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0025_collection_initial_data'),
        ('wagtaildocs', '0004_capitalizeverbose'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='collection',
            field=models.ForeignKey(related_name='+', to='wagtailcore.Collection', verbose_name='collection', default=wagtail.core.models.get_root_collection_id, on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
