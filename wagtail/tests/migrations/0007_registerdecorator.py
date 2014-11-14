# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0006_merge'),
    ]

    operations = [
        migrations.CreateModel(
            name='RegisterDecorator',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
