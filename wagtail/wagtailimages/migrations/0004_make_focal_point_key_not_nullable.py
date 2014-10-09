# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def remove_duplicate_renditions(apps, schema_editor):
    schema_editor.execute("""
        DELETE FROM wagtailimages_rendition WHERE image_id || '-' || filter_id IN (
            SELECT image_id || '-' || filter_id FROM wagtailimages_rendition WHERE focal_point_key IS NULL GROUP BY image_id, filter_id HAVING COUNT(*) > 1
        ) AND focal_point_key IS NULL
    """)

class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0003_fix_focal_point_fields'),
    ]

    operations = [
        migrations.RunPython(remove_duplicate_renditions),
        migrations.AlterField(
            model_name='rendition',
            name='focal_point_key',
            field=models.CharField(blank=True, default='', max_length=255, editable=False),
        ),
    ]
