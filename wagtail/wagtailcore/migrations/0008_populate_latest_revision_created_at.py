# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def populate_latest_revision_created_at(apps, schema_editor):
    Page = apps.get_model('wagtailcore.Page')

    for page in Page.objects.all():
        latest_revision = page.revisions.order_by('-created_at').first()

        if latest_revision is not None:
            page.latest_revision_created_at = latest_revision.created_at
            page.save(update_fields=['latest_revision_created_at'])


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0007_page_latest_revision_created_at'),
    ]

    operations = [
        migrations.RunPython(populate_latest_revision_created_at),
    ]
