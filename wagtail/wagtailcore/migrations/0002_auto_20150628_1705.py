# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('wagtailcore', '0001_squashed_0016_change_page_url_path_to_text_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='pageviewrestriction',
            name='groups',
            field=models.ManyToManyField(blank=True, null=True, to='auth.Group'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='pageviewrestriction',
            name='restriction_type',
            field=models.CharField(default='password', choices=[('none', 'Public'), ('password', 'Private, accessible with the following password'), ('users_groups', 'Private, visible to specific users and groups')], max_length=20),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='pageviewrestriction',
            name='users',
            field=models.ManyToManyField(blank=True, null=True, to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='pageviewrestriction',
            name='password',
            field=models.CharField(blank=True, verbose_name='Password', max_length=255),
            preserve_default=True,
        ),
    ]
