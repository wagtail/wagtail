# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-10 10:31
from django.db import migrations, models
import django.db.models.deletion
import wagtail.contrib.wagtailroutablepage.models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0028_merge'),
        ('routablepagetests', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RoutablePageWithOverriddenIndexRouteTest',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
            ],
            options={
                'abstract': False,
            },
            bases=(wagtail.contrib.wagtailroutablepage.models.RoutablePageMixin, 'wagtailcore.page'),
        ),
    ]
