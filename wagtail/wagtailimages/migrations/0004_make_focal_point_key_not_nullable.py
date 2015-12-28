# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def remove_duplicate_renditions(apps, schema_editor):
    if schema_editor.connection.vendor == 'mysql':
        schema_editor.execute("""
            DELETE FROM `wagtailimages_rendition` WHERE CONCAT(image_id, '-', filter_id) IN (
                SELECT CONCAT(image_id, '-', filter_id)
                FROM (SELECT * FROM `wagtailimages_rendition`) AS x
                WHERE `focal_point_key` IS NULL
                GROUP BY image_id, filter_id
                HAVING COUNT(*) > 1
            ) AND `focal_point_key` IS NULL
        """)
    elif schema_editor.connection.vendor == 'microsoft':
        schema_editor.execute("""
            DELETE FROM [wagtailimages_rendition] WHERE CAST(image_id AS VARCHAR(MAX)) + '-' +
            CAST(filter_id AS VARCHAR(MAX)) IN (
                SELECT CAST(image_id AS VARCHAR(MAX)) + '-' + CAST(filter_id AS VARCHAR(MAX))
                FROM [wagtailimages_rendition] WHERE focal_point_key IS NULL GROUP BY image_id,
                filter_id HAVING COUNT(*) > 1
            ) AND focal_point_key IS NULL
        """)
        schema_editor.execute("""
            DECLARE @constraint_name VARCHAR(MAX)
            SELECT @constraint_name = CONSTRAINT_NAME FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
            WHERE TABLE_NAME='wagtailimages_rendition' AND CONSTRAINT_TYPE='UNIQUE'
            EXEC('ALTER TABLE [wagtailimages_rendition] DROP CONSTRAINT ' + @constraint_name)
            ALTER TABLE [wagtailimages_rendition] ALTER COLUMN [focal_point_key] NVARCHAR(255) NOT NULL
            EXEC('ALTER TABLE [wagtailimages_rendition] ADD CONSTRAINT ' + @constraint_name +
            ' UNIQUE NONCLUSTERED (image_id, filter_id, focal_point_key)')
        """)
    else:
        schema_editor.execute("""
            DELETE FROM wagtailimages_rendition WHERE image_id || '-' || filter_id IN (
                SELECT image_id || '-' || filter_id FROM wagtailimages_rendition
                WHERE focal_point_key IS NULL GROUP BY image_id, filter_id HAVING COUNT(*) > 1
            ) AND focal_point_key IS NULL
        """)


def reverse_remove_duplicate_renditions(*args, **kwargs):
    """This is a no-op. The migration removes duplicates, we cannot recreate those duplicates."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0003_fix_focal_point_fields'),
    ]

    operations = [
        migrations.RunPython(remove_duplicate_renditions, reverse_remove_duplicate_renditions),

        migrations.AlterField(
            model_name='rendition',
            name='focal_point_key',
            field=models.CharField(blank=True, default='', max_length=255, editable=False),
        ),
    ]
