# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailusers', '0004_capitalizeverbose'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='show_welcome_screen',
            field=models.BooleanField(help_text='Show welcome screen on every login', default=True, verbose_name='Welcome screen'),
        ),
    ]
