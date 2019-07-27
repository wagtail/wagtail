# -*- coding: utf-8 -*-
import swapper
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailredirects', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='redirect',
            options={'verbose_name': 'Redirect'},
        ),
        migrations.AlterField(
            model_name='redirect',
            name='site',
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                related_name='redirects', blank=True, editable=False,
                to=swapper.get_model_name('wagtailcore', 'Site'),
                null=True, verbose_name='Site'
            ),
        ),
    ]
