# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0023_alter_page_revision_on_delete_behaviour"),
    ]

    operations = [
        migrations.CreateModel(
            name="Collection",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("path", models.CharField(max_length=255, unique=True)),
                ("depth", models.PositiveIntegerField()),
                ("numchild", models.PositiveIntegerField(default=0)),
                ("name", models.CharField(max_length=255, verbose_name="name")),
            ],
            options={
                "verbose_name": "collection",
                "verbose_name_plural": "collections",
            },
            bases=(models.Model,),
        ),
    ]
