# Generated by Django 5.0.9 on 2024-10-09 16:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tests", "0041_alter_jsonstreammodel_options"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customdocument",
            name="file_size",
            field=models.PositiveBigIntegerField(editable=False, null=True),
        ),
        migrations.AlterField(
            model_name="customdocumentwithauthor",
            name="file_size",
            field=models.PositiveBigIntegerField(editable=False, null=True),
        ),
        migrations.AlterField(
            model_name="customrestaurantdocument",
            name="file_size",
            field=models.PositiveBigIntegerField(editable=False, null=True),
        ),
    ]
