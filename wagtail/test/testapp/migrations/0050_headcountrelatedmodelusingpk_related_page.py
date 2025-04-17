# Generated by Django 6.0.dev20250303103700 on 2025-03-21 07:17

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tests", "0049_promotionalpage"),
        ("wagtailcore", "0094_alter_page_locale"),
    ]

    operations = [
        migrations.AddField(
            model_name="headcountrelatedmodelusingpk",
            name="related_page",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="head_count_relations",
                to="wagtailcore.page",
            ),
        ),
    ]
