# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0008_populate_latest_revision_created_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pagerevision",
            name="created_at",
            field=models.DateTimeField(),
        ),
    ]
