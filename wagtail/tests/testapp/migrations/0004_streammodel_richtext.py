# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
import wagtail.wagtailimages.blocks
import wagtail.wagtailcore.blocks
import wagtail.wagtailcore.fields


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0003_streammodel'),
    ]

    operations = [
        migrations.AlterField(
            model_name='streammodel',
            name='body',
            field=wagtail.wagtailcore.fields.StreamField(
                (
                    ('text', wagtail.wagtailcore.blocks.CharBlock()),
                    ('rich_text', wagtail.wagtailcore.blocks.RichTextBlock()),
                    ('image', wagtail.wagtailimages.blocks.ImageChooserBlock())
                )
            ),
            preserve_default=True,
        ),
    ]
