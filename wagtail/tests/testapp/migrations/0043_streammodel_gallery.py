# Generated by Django 2.0.4 on 2018-05-29 11:18

from django.db import migrations
import wagtail.core.blocks
import wagtail.core.fields
import wagtail.images.blocks


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0042_simplechildpage_simpleparentpage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='streammodel',
            name='body',
            field=wagtail.core.fields.StreamField([('text', wagtail.core.blocks.CharBlock()), ('rich_text', wagtail.core.blocks.RichTextBlock()), ('image', wagtail.images.blocks.ImageChooserBlock()), ('struct', wagtail.core.blocks.StructBlock([('image', wagtail.images.blocks.ImageChooserBlock()), ('image_list', wagtail.core.blocks.ListBlock(wagtail.images.blocks.ImageChooserBlock())), ('struct_list', wagtail.core.blocks.ListBlock(wagtail.core.blocks.StructBlock([('image', wagtail.images.blocks.ImageChooserBlock())])))])), ('gallery', wagtail.core.blocks.StreamBlock([('image', wagtail.images.blocks.ImageChooserBlock()), ('image_with_caption', wagtail.core.blocks.StructBlock([('image', wagtail.images.blocks.ImageChooserBlock()), ('caption', wagtail.core.blocks.CharBlock())]))]))]),
        ),
    ]
