# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Redirect',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('old_path', models.CharField(unique=True, max_length=255, verbose_name='Redirect from', db_index=True)),
                ('is_permanent', models.BooleanField(default=True, help_text="Recommended. Permanent redirects ensure search engines forget the old page (the 'Redirect from') and index the new page instead.", verbose_name='Permanent')),
                ('redirect_link', models.URLField(verbose_name='Redirect to any URL', blank=True)),
                ('redirect_page', models.ForeignKey(verbose_name='Redirect to a page', blank=True, to='wagtailcore.Page', null=True)),
                ('site', models.ForeignKey(blank=True, editable=False, to='wagtailcore.Site', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
