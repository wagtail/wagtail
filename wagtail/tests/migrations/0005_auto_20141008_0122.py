# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0006_auto_20141008_0420'),
        ('tests', '0004_auto_20141008_0420'),
    ]

    operations = [
        migrations.CreateModel(
            name='PageChooserModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('page', models.ForeignKey(help_text=b'help text', to='wagtailcore.Page')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SnippetChooserModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('advert', models.ForeignKey(help_text=b'help text', to='tests.Advert')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
