# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailforms', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='formsubmission',
            options={'verbose_name': 'Form Submission'},
        ),
        migrations.AlterField(
            model_name='formsubmission',
            name='submit_time',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Submit time'),
        ),
    ]
