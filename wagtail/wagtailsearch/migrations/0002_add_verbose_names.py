# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailsearch', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='editorspick',
            options={'ordering': ('sort_order',), 'verbose_name': "Editor's Pick"},
        ),
        migrations.AlterModelOptions(
            name='querydailyhits',
            options={'verbose_name': 'Query Daily Hits'},
        ),
        migrations.AlterField(
            model_name='editorspick',
            name='description',
            field=models.TextField(verbose_name='Description', blank=True),
        ),
        migrations.AlterField(
            model_name='editorspick',
            name='page',
            field=models.ForeignKey(on_delete=models.CASCADE, verbose_name='Page', to='wagtailcore.Page'),
        ),
    ]
