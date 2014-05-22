# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '__first__'),
        ('wagtaildocs', '__first__'),
        ('tests', '0003_eventpagerelatedlink'),
        ('wagtailcore', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventPageSpeaker',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('link_external', models.URLField(verbose_name=b'External link', blank=True)),
                ('link_page', models.ForeignKey(to_field='id', blank=True, to='wagtailcore.Page', null=True)),
                ('link_document', models.ForeignKey(to_field='id', blank=True, to='wagtaildocs.Document', null=True)),
                ('page', modelcluster.fields.ParentalKey(to='tests.EventPage', to_field='page_ptr')),
                ('first_name', models.CharField(max_length=255, verbose_name=b'Name', blank=True)),
                ('last_name', models.CharField(max_length=255, verbose_name=b'Surname', blank=True)),
                ('image', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to_field='id', blank=True, to='wagtailimages.Image', null=True)),
            ],
            options={
                'ordering': [b'sort_order'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SimplePage',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, primary_key=True, to_field='id', serialize=False, to='wagtailcore.Page')),
                ('content', models.TextField()),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
    ]
