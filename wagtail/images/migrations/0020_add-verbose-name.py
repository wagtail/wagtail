# Generated by Django 2.0.3 on 2018-03-17 17:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("wagtailimages", "0019_delete_filter")]

    operations = [
        migrations.AlterModelOptions(
            name="image",
            options={"verbose_name": "image", "verbose_name_plural": "images"},
        )
    ]
