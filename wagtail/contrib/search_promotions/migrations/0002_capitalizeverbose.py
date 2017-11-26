# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailsearchpromotions', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='searchpromotion',
            options={'ordering': ('sort_order',), 'verbose_name': 'search promotion'},
        ),
        migrations.AlterField(
            model_name='searchpromotion',
            name='description',
            field=models.TextField(blank=True, verbose_name='description'),
        ),
        migrations.AlterField(
            model_name='searchpromotion',
            name='page',
            field=models.ForeignKey(on_delete=models.CASCADE, to='wagtailcore.Page', verbose_name='page'),
        ),
    ]
