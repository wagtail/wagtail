# Generated by Django 4.0.10 on 2023-08-04 09:09

from django.db import migrations
from django.contrib.postgres.operations import TrigramExtension

def add_trigram_extension_for_postgres(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        return TrigramExtension()


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailsearch', '0007_delete_editorspick'),
    ]

    operations = [
        migrations.RunPython(add_trigram_extension_for_postgres)
    ]
