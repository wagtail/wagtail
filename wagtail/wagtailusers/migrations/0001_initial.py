# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('submitted_notifications', models.BooleanField(
                    default=True,
                    help_text='Receive notification when a page is submitted for moderation'
                )),
                ('approved_notifications', models.BooleanField(
                    default=True,
                    help_text='Receive notification when your page edit is approved'
                )),
                ('rejected_notifications', models.BooleanField(
                    default=True,
                    help_text='Receive notification when your page edit is rejected'
                )),
                ('user', models.OneToOneField(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
