# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0002_initial_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='Redirect',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('old_path', models.CharField(
                    verbose_name='Redirect from', max_length=255, unique=True, db_index=True
                )),
                ('is_permanent', models.BooleanField(
                    verbose_name='Permanent', default=True, help_text="""Recommended. Permanent redirects \
                    ensure search engines forget the old page (the 'Redirect from') and index the new page instead."""
                )),
                ('redirect_link', models.URLField(blank=True, verbose_name='Redirect to any URL')),
                ('redirect_page', models.ForeignKey(
                    blank=True, null=True, verbose_name='Redirect to a page', to='wagtailcore.Page'
                )),
                ('site', models.ForeignKey(
                    blank=True, to='wagtailcore.Site', editable=False, null=True, related_name='redirects'
                )),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
