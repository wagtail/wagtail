# Generated by Django 4.0.3 on 2022-03-06 13:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailimages", "0023_add_choose_permissions"),
    ]

    operations = [
        migrations.DeleteModel(
            name="UploadedImage",
        ),
    ]
