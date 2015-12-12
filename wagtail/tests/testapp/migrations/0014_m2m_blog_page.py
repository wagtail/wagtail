# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import wagtail.wagtailcore.fields
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0020_add_index_on_page_first_published_at'),
        ('tests', '0013_iconsetting_notyetregisteredsetting_testsetting'),
    ]

    operations = [
        migrations.CreateModel(
            name='BlogCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(unique=True, max_length=80)),
            ],
        ),
        migrations.CreateModel(
            name='BlogCategoryBlogPage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('category', models.ForeignKey(to='tests.BlogCategory', related_name='+')),
            ],
        ),
        migrations.CreateModel(
            name='ManyToManyBlogPage',
            fields=[
                (
                    'page_ptr',
                    models.OneToOneField(
                        primary_key=True,
                        serialize=False,
                        parent_link=True,
                        auto_created=True,
                        to='wagtailcore.Page'
                    )
                ),
                ('body', wagtail.wagtailcore.fields.RichTextField(blank=True)),
                ('adverts', models.ManyToManyField(to='tests.Advert', blank=True)),
                (
                    'blog_categories',
                    models.ManyToManyField(
                        to='tests.BlogCategory',
                        through='tests.BlogCategoryBlogPage',
                        blank=True
                    )
                ),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.AddField(
            model_name='blogcategoryblogpage',
            name='page',
            field=modelcluster.fields.ParentalKey(to='tests.ManyToManyBlogPage', related_name='categories'),
        ),
    ]
