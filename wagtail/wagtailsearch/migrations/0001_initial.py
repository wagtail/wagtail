# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0002_initial_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='EditorsPick',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('sort_order', models.IntegerField(blank=True, null=True, editable=False)),
                ('description', models.TextField(blank=True)),
                ('page', models.ForeignKey(on_delete=models.CASCADE, to='wagtailcore.Page')),
            ],
            options={
                'ordering': ('sort_order',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Query',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('query_string', models.CharField(unique=True, max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='QueryDailyHits',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('date', models.DateField()),
                ('hits', models.IntegerField(default=0)),
                ('query', models.ForeignKey(on_delete=models.CASCADE, to='wagtailsearch.Query', related_name='daily_hits')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='querydailyhits',
            unique_together=set([('query', 'date')]),
        ),
        migrations.AddField(
            model_name='editorspick',
            name='query',
            field=models.ForeignKey(on_delete=models.CASCADE, to='wagtailsearch.Query', related_name='editors_picks'),
            preserve_default=True,
        ),
    ]
