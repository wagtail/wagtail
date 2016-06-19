# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def forwards_data_migration(apps, schema_editor):
    Rendition = apps.get_model('wagtailimages', 'Rendition')
    db_alias = schema_editor.connection.alias
    # update doesn't work during migration, we have to do it one by one
    for rendition in Rendition.objects.using(db_alias).select_related('filter').all():
        rendition.filter2 = rendition.filter.spec
        rendition.save()


def reverse_data_migration(apps, schema_editor):
    Rendition = apps.get_model('wagtailimages', 'Rendition')
    Filter = apps.get_model('wagtailimages', 'Filter')
    db_alias = schema_editor.connection.alias
    renditions = Rendition.objects.using(db_alias).all()
    for rendition in renditions:
        # Ensure we don't create the same Filter twice
        rendition.filter, _ = Filter.objects.get_or_create(spec=rendition.filter2)
        rendition.save()


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0014_remove_filter_model_1'),
    ]

    operations = [
        # Migrate data.
        migrations.RunPython(forwards_data_migration, reverse_data_migration),
    ]
