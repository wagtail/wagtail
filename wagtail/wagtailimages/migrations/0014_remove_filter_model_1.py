# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0013_make_rendition_upload_callable'),
    ]

    operations = [
        # We create a new attribute to allow the data migration (filter -> filter2).
        migrations.AddField(
            model_name='Rendition',
            name='filter2',
            field=models.CharField(max_length=255, default=''),
            preserve_default=False,
        ),
        # Allow NULL for backward operation to work (no temporary default value possible as the `spec` attribute is not null but also unique).
        migrations.AlterField('rendition', 'filter', models.ForeignKey(on_delete=models.CASCADE, related_name='+', to='wagtailimages.Filter', null=True)),
        # Remove unique constraint to allow the removal of `filter` field.
        migrations.AlterUniqueTogether('rendition', set([])),
    ]
