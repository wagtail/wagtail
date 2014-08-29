# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0002_initial_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='PagePublishLog',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
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
            field=models.ForeignKey(null=True, related_name='+', editable=False, to='wagtailcore.PagePublishLog'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='page',
            name='last_publish',
            field=models.ForeignKey(null=True, related_name='+', editable=False, to='wagtailcore.PagePublishLog'),
            preserve_default=True,
        ),
    ]
