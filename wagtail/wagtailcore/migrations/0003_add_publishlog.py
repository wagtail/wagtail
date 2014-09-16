# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0002_initial_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='PagePublishLog',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('published_at', models.DateTimeField()),
                ('page', models.ForeignKey(related_name='publish_log', to='wagtailcore.Page')),
                ('revision', models.ForeignKey(related_name='publish_log', to='wagtailcore.PageRevision')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='page',
            name='first_publish',
            field=models.ForeignKey(related_name='+', to='wagtailcore.PagePublishLog', on_delete=django.db.models.deletion.SET_NULL, editable=False, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='page',
            name='last_publish',
            field=models.ForeignKey(related_name='+', to='wagtailcore.PagePublishLog', on_delete=django.db.models.deletion.SET_NULL, editable=False, null=True),
            preserve_default=True,
        ),
    ]
