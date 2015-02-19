# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0008_registerdecorator'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventPageChooserModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('page', models.ForeignKey(help_text=b'more help text', to='tests.EventPage')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
