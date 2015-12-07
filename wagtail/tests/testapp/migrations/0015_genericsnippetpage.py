# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0020_add_index_on_page_first_published_at'),
        ('contenttypes', '0001_initial'),
        ('tests', '0014_m2m_blog_page'),
    ]

    operations = [
        migrations.CreateModel(
            name='GenericSnippetPage',
            fields=[
                (
                    'page_ptr',
                    models.OneToOneField(
                        primary_key=True,
                        parent_link=True,
                        auto_created=True,
                        to='wagtailcore.Page',
                        serialize=False
                    )
                ),
                ('snippet_object_id', models.PositiveIntegerField(null=True)),
                (
                    'snippet_content_type',
                    models.ForeignKey(
                        null=True,
                        to='contenttypes.ContentType',
                        on_delete=django.db.models.deletion.SET_NULL
                    )
                ),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
    ]
