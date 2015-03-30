# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0013_update_golive_expire_help_text'),
        ('wagtailforms', '0001_initial'),
        ('wagtailredirects', '0001_initial'),
        ('wagtailsearch', '0001_initial'),
        ('tests', '0012_auto_20150330_0709'),
    ]

    operations = [
        migrations.DeleteModel(
            name='RoutablePageTest',
        ),
    ]
