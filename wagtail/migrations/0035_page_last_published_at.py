# Generated by Django 1.11.1 on 2017-05-22 13:35
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0034_page_live_revision"),
    ]

    operations = [
        migrations.AddField(
            model_name="page",
            name="last_published_at",
            field=models.DateTimeField(
                editable=False, null=True, verbose_name="last published at"
            ),
        ),
    ]
