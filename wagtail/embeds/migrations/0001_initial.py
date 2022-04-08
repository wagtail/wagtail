# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Embed",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        auto_created=True,
                        serialize=False,
                    ),
                ),
                ("url", models.URLField()),
                ("max_width", models.SmallIntegerField(null=True, blank=True)),
                (
                    "type",
                    models.CharField(
                        max_length=10,
                        choices=[
                            ("video", "Video"),
                            ("photo", "Photo"),
                            ("link", "Link"),
                            ("rich", "Rich"),
                        ],
                    ),
                ),
                ("html", models.TextField(blank=True)),
                ("title", models.TextField(blank=True)),
                ("author_name", models.TextField(blank=True)),
                ("provider_name", models.TextField(blank=True)),
                ("thumbnail_url", models.URLField(null=True, blank=True)),
                ("width", models.IntegerField(null=True, blank=True)),
                ("height", models.IntegerField(null=True, blank=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name="embed",
            unique_together={("url", "max_width")},
        ),
    ]
