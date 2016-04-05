# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customuser', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='customuser',
            old_name='id',
            new_name='identifier'
        ),
        migrations.AlterField(
            model_name='customuser',
            name='identifier',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]
