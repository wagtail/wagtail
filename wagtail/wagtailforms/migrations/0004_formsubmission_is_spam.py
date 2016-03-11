# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailforms', '0003_capitalizeverbose'),
    ]

    operations = [
        migrations.AddField(
            model_name='formsubmission',
            name='is_spam',
            field=models.BooleanField(default=False, verbose_name='is spam'),
            preserve_default=False,
        ),
    ]
