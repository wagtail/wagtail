from django.db import migrations


def initial_data(apps, schema_editor):
    Collection = apps.get_model("wagtailcore.Collection")
    db = schema_editor.connection.alias

    # Create root page
    Collection.objects.using(db).create(
        name="Root",
        path="0001",
        depth=1,
        numchild=0,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0024_collection"),
    ]

    operations = [
        migrations.RunPython(initial_data, migrations.RunPython.noop),
    ]
