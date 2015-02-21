# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0010_change_page_owner_to_null_on_delete'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='expire_at',
            field=models.DateTimeField(help_text='Please add a date-time in the form YYYY-MM-DD hh:mm.', null=True, verbose_name='Expiry date/time', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='page',
            name='go_live_at',
            field=models.DateTimeField(help_text='Please add a date-time in the form YYYY-MM-DD hh:mm.', null=True, verbose_name='Go live date/time', blank=True),
            preserve_default=True,
        ),
    ]
