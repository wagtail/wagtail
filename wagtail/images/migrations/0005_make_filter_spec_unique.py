# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailimages", "0004_make_focal_point_key_not_nullable"),
    ]

    operations = [
        migrations.AlterField(
            model_name="filter",
            name="spec",
            field=models.CharField(unique=True, max_length=255),
            preserve_default=True,
        ),
    ]
