from django.db import migrations, models

from wagtail.embeds.embeds import get_embed_hash


def migrate_forwards(apps, schema_editor):
    Embed = apps.get_model("wagtailembeds.Embed")

    # based each embed being ~500b, available memory being
    # to 2MB, and leaving plenty of headway for app itself
    batch_size = 1500

    # allows small batches to be kept in memory in order
    # to utilise bulk_update()
    batch = []

    for embed in Embed.objects.all().only("id", "url", "max_width").iterator():

        embed.hash = get_embed_hash(embed.url, embed.max_width)
        batch.append(embed)

        if len(batch) == batch_size:
            # save and reset current batch
            Embed.objects.bulk_update(batch, ["hash"])
            batch.clear()

    # save any leftovers
    if batch:
        Embed.objects.bulk_update(batch, ["hash"])


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailembeds", "0005_specify_thumbnail_url_max_length"),
    ]

    operations = [
        migrations.AddField(
            model_name="embed",
            name="hash",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.RunPython(migrate_forwards, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="embed",
            name="hash",
            field=models.CharField(db_index=True, max_length=32, unique=True),
        ),
        # MySQL needs max length on the unique together fields.
        # Drop unique together before alter char to text.
        migrations.AlterUniqueTogether(
            name="embed",
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name="embed",
            name="url",
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name="embed",
            name="thumbnail_url",
            field=models.TextField(
                blank=True,
                default="",
            ),
            preserve_default=False,
        ),
    ]
