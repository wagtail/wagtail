# Generated by Django 1.9.7 on 2016-06-07 11:22
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("modeladmintest", "0002_token"),
    ]

    operations = [
        migrations.CreateModel(
            name="Publisher",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50)),
                (
                    "headquartered_in",
                    models.CharField(max_length=50, null=True, blank=True),
                ),
            ],
        ),
    ]
