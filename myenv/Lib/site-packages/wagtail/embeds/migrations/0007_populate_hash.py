from django.db import migrations
from django.db.models import Count, Min

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

    # delete duplicates
    duplicates = (
        Embed.objects.values("hash")
        .annotate(hash_count=Count("id"), min_id=Min("id"))
        .filter(hash_count__gt=1)
    )
    for dup in duplicates:
        # for each duplicated hash, delete all except the one with the lowest id
        Embed.objects.filter(hash=dup["hash"]).exclude(id=dup["min_id"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailembeds", "0006_add_embed_hash"),
    ]

    operations = [
        migrations.RunPython(migrate_forwards, migrations.RunPython.noop),
    ]
