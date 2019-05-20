# Generated by Django 2.0.4 on 2018-04-12 15:10

from django.db import migrations, models
import django.db.models.deletion
import wagtail.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0040_page_draft_title"),
        ("tests", "0029_auto_20180215_1950"),
    ]

    operations = [
        migrations.CreateModel(
            name="FormClassAdditionalFieldPage",
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
                ("location", models.CharField(max_length=255)),
                ("body", wagtail.core.fields.RichTextField(blank=True)),
            ],
            options={"abstract": False},
            bases=("wagtailcore.page",),
        )
    ]
