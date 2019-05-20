# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-03-01 21:32
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0028_merge'),
        ('tests', '0002_customimage_collections'),
    ]

    operations = [
        migrations.CreateModel(
            name='OneToOnePage',
            fields=[
                (
                    'page_ptr',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        related_name='+',
                        serialize=False,
                        to='wagtailcore.Page',
                    ),
                )
            ],
            options={'abstract': False},
            bases=('wagtailcore.page',),
        )
    ]
