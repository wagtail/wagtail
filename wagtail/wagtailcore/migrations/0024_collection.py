# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def set_collection_path_collation(apps, schema_editor):
    """
    Treebeard's path comparison logic can fail on certain locales such as sk_SK, which
    sort numbers after letters. To avoid this, we explicitly set the collation for the
    'path' column to the (non-locale-specific) 'C' collation.

    See: https://groups.google.com/d/msg/wagtail/q0leyuCnYWI/I9uDvVlyBAAJ
    """
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute("""
            ALTER TABLE wagtailcore_collection ALTER COLUMN path TYPE VARCHAR(255) COLLATE "C"
        """)


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0023_alter_page_revision_on_delete_behaviour'),
    ]

    operations = [
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('path', models.CharField(max_length=255, unique=True)),
                ('depth', models.PositiveIntegerField()),
                ('numchild', models.PositiveIntegerField(default=0)),
                ('name', models.CharField(max_length=255, verbose_name='name')),
            ],
            options={
                'verbose_name': 'collection',
                'verbose_name_plural': 'collections',
            },
            bases=(models.Model,),
        ),
        migrations.RunPython(
            set_collection_path_collation, migrations.RunPython.noop
        ),
    ]
