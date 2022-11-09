# Generated by Django 4.1.3 on 2022-11-09 11:06

from django.db import migrations
import wagtail.blocks
import wagtail.fields
import wagtail.test.testapp.models


class Migration(migrations.Migration):

    dependencies = [
        ("tests", "0010_alter_customimage_file_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="streampage",
            name="body",
            field=wagtail.fields.StreamField(
                [
                    ("text", wagtail.blocks.CharBlock()),
                    ("rich_text", wagtail.blocks.RichTextBlock()),
                    ("image", wagtail.test.testapp.models.ExtendedImageChooserBlock()),
                    (
                        "product",
                        wagtail.blocks.StructBlock(
                            [
                                ("name", wagtail.blocks.CharBlock()),
                                ("price", wagtail.blocks.CharBlock()),
                            ]
                        ),
                    ),
                    ("raw_html", wagtail.blocks.RawHTMLBlock()),
                    (
                        "books",
                        wagtail.blocks.StreamBlock(
                            [
                                ("title", wagtail.blocks.CharBlock()),
                                ("author", wagtail.blocks.CharBlock()),
                            ]
                        ),
                    ),
                    (
                        "title_list",
                        wagtail.blocks.ListBlock(wagtail.blocks.CharBlock()),
                    ),
                ],
                use_json_field=False,
            ),
        ),
    ]
