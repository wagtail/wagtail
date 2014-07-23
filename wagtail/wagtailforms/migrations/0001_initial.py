# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FormSubmission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('form_data', models.TextField()),
                ('submit_time', models.DateTimeField(auto_now_add=True)),
                ('page', models.ForeignKey(to='wagtailcore.Page')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
