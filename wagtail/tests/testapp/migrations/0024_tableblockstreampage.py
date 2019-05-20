# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-12-03 08:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import wagtail.contrib.table_block.blocks
import wagtail.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0040_page_draft_title"),
        ("tests", "0023_formpagewithredirect_redirectformfield"),
    ]

    operations = [
        migrations.CreateModel(
            name="TableBlockStreamPage",
            fields=[
                (
                    "page_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="wagtailcore.Page",
                    ),
                ),
                (
                    "table",
                    wagtail.core.fields.StreamField(
                        (("table", wagtail.contrib.table_block.blocks.TableBlock()),)
                    ),
                ),
            ],
            options={"abstract": False},
            bases=("wagtailcore.page",),
        )
    ]
