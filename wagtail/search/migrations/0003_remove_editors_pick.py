# -*- coding: utf-8 -*-
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("wagtailsearch", "0002_add_verbose_names"),
    ]

    operations = [
        # Do nothing. Previously this migration dropped the EditorsPick model from the application
        # state but kept the database intact so that the wagtail.contrib.search_promotions app
        # could subsequently adopt it by renaming the table. wagtail.contrib.search_promotions
        # now creates its own table, so we don't want to keep the table from wagtailsearch around;
        # we will delete it properly in wagtailsearch migration 0007.
        # See https://github.com/wagtail/wagtail/issues/1824#issuecomment-1271840741
    ]
