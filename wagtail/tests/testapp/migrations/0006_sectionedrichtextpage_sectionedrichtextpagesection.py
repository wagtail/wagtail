# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import modelcluster.fields
import wagtail.wagtailcore.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0028_merge'),
        ('tests', '0005_customrichblockfieldpage_customrichtextfieldpage_defaultrichblockfieldpage_defaultrichtextfieldpage'),
    ]

    operations = [
        migrations.CreateModel(
            name='SectionedRichTextPage',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, to='wagtailcore.Page', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='SectionedRichTextPageSection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('sort_order', models.IntegerField(editable=False, null=True, blank=True)),
                ('body', wagtail.wagtailcore.fields.RichTextField()),
                ('page', modelcluster.fields.ParentalKey(related_name='sections', to='tests.SectionedRichTextPage')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
    ]
