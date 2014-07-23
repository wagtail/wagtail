# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EditorsPick',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('description', models.TextField(blank=True)),
                ('page', models.ForeignKey(to='wagtailcore.Page')),
            ],
            options={
                'ordering': (b'sort_order',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Query',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('query_string', models.CharField(unique=True, max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='editorspick',
            name='query',
            field=models.ForeignKey(to='wagtailsearch.Query'),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='QueryDailyHits',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('hits', models.IntegerField(default=0)),
                ('query', models.ForeignKey(to='wagtailsearch.Query')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='querydailyhits',
            unique_together=set([(b'query', b'date')]),
        ),
    ]
