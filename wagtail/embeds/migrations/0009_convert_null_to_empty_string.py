from django.db import migrations


def migrate_forwards(apps, schema_editor):
    Embed = apps.get_model("wagtailembeds.Embed")

    Embed.objects.filter(thumbnail_url__isnull=True).all().update(thumbnail_url='')


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailembeds", "0008_allow_long_urls"),
    ]

    operations = [
        migrations.RunPython(migrate_forwards, migrations.RunPython.noop),
    ]
