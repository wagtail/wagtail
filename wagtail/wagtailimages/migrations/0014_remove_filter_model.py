# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


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
        # Migrate data.
        migrations.RunPython(forwards_data_migration, reverse_data_migration),
        # We can now delete Filter for good.
        migrations.RemoveField(model_name='Rendition', name='filter'),
        migrations.DeleteModel('Filter'),
        # And we can finally set the new attribute as `filter`.
        migrations.RenameField(model_name='Rendition', old_name='filter2', new_name='filter'),
        # Bug with mysql and postgresql, we need to add the index after the renaming (https://code.djangoproject.com/ticket/25530).
        migrations.AlterField('rendition', 'filter', models.CharField(max_length=255, db_index=True)),
        # We can now set back the unique constraint.
        migrations.AlterUniqueTogether('rendition', set([('image', 'filter', 'focal_point_key')])),
    ]
