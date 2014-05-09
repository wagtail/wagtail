# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wagtaildocs', '__first__'),
        ('wagtailcore', '__first__'),
        ('tests', '0002_eventpagecarouselitem'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventPageRelatedLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('link_external', models.URLField(verbose_name=b'External link', blank=True)),
                ('link_page', models.ForeignKey(to_field='id', blank=True, to='wagtailcore.Page', null=True)),
                ('link_document', models.ForeignKey(to_field='id', blank=True, to='wagtaildocs.Document', null=True)),
                ('title', models.CharField(help_text=b'Link title', max_length=255)),
                ('page', modelcluster.fields.ParentalKey(to='tests.EventPage', to_field='page_ptr')),
            ],
            options={
                'ordering': [b'sort_order'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
