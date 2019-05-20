# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-02 01:03
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0040_page_draft_title'),
        ('tests', '0021_hidden_form_field'),
    ]

    operations = [
        migrations.CreateModel(
            name='PageWithExcludedCopyField',
            fields=[
                (
                    'page_ptr',
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to='wagtailcore.Page',
                    ),
                ),
                ('content', models.TextField()),
                (
                    'special_field',
                    models.CharField(
                        blank=True, default='Very Special', max_length=255
                    ),
                ),
            ],
            options={'abstract': False},
            bases=('wagtailcore.page',),
        )
    ]
