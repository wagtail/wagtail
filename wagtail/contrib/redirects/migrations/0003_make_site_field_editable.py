# -*- coding: utf-8 -*-
import swapper
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailredirects', '0002_add_verbose_names'),
    ]

    operations = [
        migrations.AlterField(
            model_name='redirect',
            name='site',
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                null=True, to=swapper.get_model_name('wagtailcore', 'Site'),
                verbose_name='Site', blank=True, related_name='redirects'
            ),
        ),
    ]
