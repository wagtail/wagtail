# Generated by Django 4.0.7 on 2022-10-19 00:20

from django.db import migrations
import wagtail.images.models


class Migration(migrations.Migration):

    dependencies = [
        ("tests", "0009_alter_eventpage_options"),
    ]

    rendition_file_options = {
        "height_field": "height",
        "upload_to": wagtail.images.models.get_rendition_upload_to,
        "width_field": "width",
        "storage": wagtail.images.models.get_rendition_storage,
    }

    operations = [
        migrations.AlterField(
            model_name="customimage",
            name="file",
            field=wagtail.images.models.WagtailImageField(
                height_field="height",
                upload_to=wagtail.images.models.get_upload_to,
                verbose_name="file",
                width_field="width",
            ),
        ),
        migrations.AlterField(
            model_name="customimagefilepath",
            name="file",
            field=wagtail.images.models.WagtailImageField(
                height_field="height",
                upload_to=wagtail.images.models.get_upload_to,
                verbose_name="file",
                width_field="width",
            ),
        ),
        migrations.AlterField(
            model_name="customimagewithauthor",
            name="file",
            field=wagtail.images.models.WagtailImageField(
                height_field="height",
                upload_to=wagtail.images.models.get_upload_to,
                verbose_name="file",
                width_field="width",
            ),
        ),
        migrations.AlterField(
            model_name="customrendition",
            name="file",
            field=wagtail.images.models.WagtailImageField(**rendition_file_options),
        ),
        migrations.AlterField(
            model_name="customrenditionwithauthor",
            name="file",
            field=wagtail.images.models.WagtailImageField(**rendition_file_options),
        ),
        migrations.AlterField(
            model_name="customrestaurantimage",
            name="file",
            field=wagtail.images.models.WagtailImageField(
                height_field="height",
                upload_to=wagtail.images.models.get_upload_to,
                verbose_name="file",
                width_field="width",
            ),
        ),
    ]
