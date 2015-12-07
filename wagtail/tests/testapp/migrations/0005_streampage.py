# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import wagtail.wagtailcore.fields
import wagtail.wagtailcore.blocks
import wagtail.wagtailimages.blocks


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0001_squashed_0016_change_page_url_path_to_text_field'),
        ('tests', '0004_streammodel_richtext'),
    ]

    operations = [
        migrations.CreateModel(
            name='StreamPage',
            fields=[
                (
                    'page_ptr',
                    models.OneToOneField(
                        auto_created=True,
                        to='wagtailcore.Page',
                        serialize=False,
                        parent_link=True,
                        primary_key=True
                    )
                ),
                (
                    'body',
                    wagtail.wagtailcore.fields.StreamField(
                        (
                            ('text', wagtail.wagtailcore.blocks.CharBlock()),
                            ('rich_text', wagtail.wagtailcore.blocks.RichTextBlock()),
                            ('image', wagtail.wagtailimages.blocks.ImageChooserBlock())
                        )
                    )
                ),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
    ]
