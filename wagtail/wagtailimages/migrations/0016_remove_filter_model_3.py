# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0015_remove_filter_model_2'),
    ]

    operations = [
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
