# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('searchtests', '0002_anothersearchtestchild'),
    ]

    operations = [
        migrations.CreateModel(
            name='SearchTestSubObject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('parent', models.ForeignKey(to='searchtests.SearchTest', related_name='subobjects', on_delete=models.deletion.CASCADE)),
                ('name', models.CharField(max_length=255)),
            ],
            bases=(models.Model,),
        ),
    ]
