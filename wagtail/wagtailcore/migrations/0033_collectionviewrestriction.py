# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-19 15:32
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0008_alter_user_username_max_length'),
        ('wagtailcore', '0032_add_bulk_delete_page_permission'),
    ]

    operations = [
        migrations.CreateModel(
            name='CollectionViewRestriction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('restriction_type', models.CharField(choices=[('none', 'Public'), ('login', 'Private, accessible to logged-in users'), ('password', 'Private, accessible with the following password'), ('groups', 'Private, accessible to users in specific groups')], max_length=20)),
                ('password', models.CharField(blank=True, max_length=255, verbose_name='password')),
                ('collection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='view_restrictions', to='wagtailcore.Collection', verbose_name='collection')),
                ('groups', models.ManyToManyField(blank=True, to='auth.Group')),
            ],
            options={
                'verbose_name': 'collection view restriction',
                'verbose_name_plural': 'collection view restrictions',
            },
        ),
    ]
