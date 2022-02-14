# -*- coding: utf-8 -*-
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailforms", "0003_capitalizeverbose"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="formsubmission",
            options={
                "verbose_name": "form submission",
                "verbose_name_plural": "form submissions",
            },
        ),
    ]
