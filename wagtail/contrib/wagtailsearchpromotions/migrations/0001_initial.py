# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0015_add_more_verbose_names'),
        ('wagtailsearch', '0003_remove_editors_pick'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='EditorsPick',
                    fields=[
                        ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID',
                         auto_created=True)),
                        ('sort_order', models.IntegerField(editable=False, null=True, blank=True)),
                        ('description', models.TextField(verbose_name='Description', blank=True)),
                        ('page', models.ForeignKey(on_delete=models.CASCADE, verbose_name='Page', to='wagtailcore.Page')),
                        ('query', models.ForeignKey(on_delete=models.CASCADE, to='wagtailsearch.Query', related_name='editors_picks')),
                    ],
                    options={
                        'db_table': 'wagtailsearch_editorspick',
                        'verbose_name': "Editor's Pick",
                        'ordering': ('sort_order',),
                    },
                ),
            ],
            database_operations=[]
        ),
        migrations.AlterModelTable(
            name='editorspick',
            table=None,
        ),
        migrations.RenameModel(
            old_name='EditorsPick',
            new_name='SearchPromotion'
        ),
        migrations.AlterModelOptions(
            name='searchpromotion',
            options={'ordering': ('sort_order',), 'verbose_name': 'Search promotion'},
        ),
    ]
