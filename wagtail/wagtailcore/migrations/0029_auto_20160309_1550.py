# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('wagtailcore', '0023_alter_page_revision_on_delete_behaviour'),
    ]

    operations = [
        migrations.AddField(
            model_name='pageviewrestriction',
            name='groups',
            field=models.ManyToManyField(to='auth.Group', blank=True),
        ),
        migrations.AddField(
            model_name='pageviewrestriction',
            name='restriction_type',
            field=models.CharField(default='none', max_length=20, choices=[('none', 'Public'), ('login', 'Private, visible if logged in'), ('password', 'Private, accessible with the following password'), ('users_groups', 'Private, visible to specific users and groups')]),
        ),
        migrations.AddField(
            model_name='pageviewrestriction',
            name='users',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AlterField(
            model_name='pageviewrestriction',
            name='password',
            field=models.CharField(max_length=255, verbose_name='password', blank=True),
        ),
    ]
