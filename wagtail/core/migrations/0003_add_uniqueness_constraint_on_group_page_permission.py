# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0002_initial_data"),
    ]

    operations = [
        migrations.AlterField(
            model_name="grouppagepermission",
            name="permission_type",
            field=models.CharField(
                max_length=20,
                choices=[
                    (b"add", b"Add/edit pages you own"),
                    (b"edit", b"Add/edit any page"),
                    (b"publish", b"Publish any page"),
                ],
            ),
        ),
        migrations.AlterUniqueTogether(
            name="grouppagepermission",
            unique_together={("group", "page", "permission_type")},
        ),
    ]
