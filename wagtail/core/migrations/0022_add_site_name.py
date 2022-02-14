# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0021_capitalizeverbose"),
    ]

    operations = [
        migrations.AddField(
            model_name="site",
            name="site_name",
            field=models.CharField(
                verbose_name="site name",
                null=True,
                blank=True,
                max_length=255,
                help_text="Human-readable name for the site.",
            ),
        ),
    ]
