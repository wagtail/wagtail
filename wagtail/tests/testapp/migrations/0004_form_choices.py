# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0003_onetoonepage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='formfield',
            name='choices',
            field=models.TextField(verbose_name='choices', help_text='Comma separated list of choices. Only applicable in checkboxes, radio and dropdown.', blank=True),
        ),
    ]
