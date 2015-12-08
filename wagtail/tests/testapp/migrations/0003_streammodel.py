# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import wagtail.wagtailcore.fields
import wagtail.wagtailcore.blocks
import wagtail.wagtailimages.blocks


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0002_add_verbose_names'),
    ]

    operations = [
        migrations.CreateModel(
            name='StreamModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                (
                    'body',
                    wagtail.wagtailcore.fields.StreamField(
                        [('text', wagtail.wagtailcore.blocks.CharBlock()),
                            ('image', wagtail.wagtailimages.blocks.ImageChooserBlock())]
                    )
                ),
            ],
        ),
    ]
