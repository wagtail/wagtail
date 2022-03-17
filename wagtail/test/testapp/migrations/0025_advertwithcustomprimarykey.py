# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django


class Migration(migrations.Migration):

    dependencies = [
        ("tests", "0024_tableblockstreampage"),
    ]

    operations = [
        migrations.CreateModel(
            name="AdvertWithCustomPrimaryKey",
            fields=[
                (
                    "advert_id",
                    models.CharField(max_length=255, primary_key=True, serialize=False),
                ),
                ("url", models.URLField(blank=True, null=True)),
                ("text", models.CharField(max_length=255)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="SnippetChooserModelWithCustomPrimaryKey",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "advertwithcustomprimarykey",
                    models.ForeignKey(
                        help_text="help text",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="tests.AdvertWithCustomPrimaryKey",
                    ),
                ),
            ],
        ),
    ]
