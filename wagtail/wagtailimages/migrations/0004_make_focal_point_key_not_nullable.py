# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def remove_duplicate_renditions(apps, schema_editor):
    Rendition = apps.get_model('wagtailimages.Rendition')

    # Find all filter_id / image_id pairings that appear multiple times in the renditions table
    # with focal_point_key = NULL
    duplicates = (
        Rendition.objects.filter(focal_point_key__isnull=True).
        values('image_id', 'filter_id').
        annotate(count_id=models.Count('id'), min_id=models.Min('id')).
        filter(count_id__gt=1)
    )

    # Delete all occurrences of those pairings, except for the one with the lowest ID
    for duplicate in duplicates:
        Rendition.objects.filter(
            focal_point_key__isnull=True,
            image=duplicate['image_id'],
            filter=duplicate['filter_id']
        ).exclude(
            id=duplicate['min_id']
        ).delete()


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
