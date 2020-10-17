# -*- coding: utf-8 -*-
import uuid
from django.db import migrations


def migrate_forwards(apps, schema_editor):
    Page = apps.get_model('wagtailcore.Page')

    # based each page being ~500b, available memory being
    # to 2MB, and leaving plenty of headway for app itself
    batch_size = 1500

    # allows small batches to be kept in memory in order
    # to utilise bulk_update()
    batch = []

    for page in Page.objects.all().only('id', 'url_path').iterator():

        # generate uuid from 'url_path' for similar results accross environments
        page.uuid = uuid.uuid3(uuid.NAMESPACE_URL, page.url_path)
        batch.append(page)

        if len(batch) == batch_size:
            # save and reset current batch
            Page.objects.bulk_update(batch, ['uuid'])
            batch.clear()

    # save any leftovers
    if batch:
        Page.objects.bulk_update(batch, ['uuid'])


def migrate_backwards(apps, schema_editor):
    Page = apps.get_model('wagtailcore.Page')
    Page.objects.all().update(uuid=None)


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0060_add_page_uuid'),
    ]

    operations = [
        migrations.RunPython(migrate_forwards, migrate_backwards),
    ]
