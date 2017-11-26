# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailforms', '0002_add_verbose_names'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='formsubmission',
            options={'verbose_name': 'form submission'},
        ),
        migrations.AlterField(
            model_name='formsubmission',
            name='submit_time',
            field=models.DateTimeField(auto_now_add=True, verbose_name='submit time'),
        ),
    ]
