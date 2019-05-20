# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-20 10:57
from django.db import migrations
import wagtail.tests.testapp.models
import wagtail.core.blocks
import wagtail.core.fields


class Migration(migrations.Migration):

    dependencies = [('tests', '0012_panelsettings_tabbedsettings')]

    operations = [
        migrations.AlterField(
            model_name='streampage',
            name='body',
            field=wagtail.core.fields.StreamField(
                [
                    ('text', wagtail.core.blocks.CharBlock()),
                    ('rich_text', wagtail.core.blocks.RichTextBlock()),
                    ('image', wagtail.tests.testapp.models.ExtendedImageChooserBlock()),
                ]
            ),
        )
    ]
