# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
import wagtail.wagtailcore.fields
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '__first__'),
        ('wagtailcore', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventIndex',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, primary_key=True, to_field='id', serialize=False, to='wagtailcore.Page')),
                ('intro', wagtail.wagtailcore.fields.RichTextField(blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='EventPage',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, primary_key=True, to_field='id', serialize=False, to='wagtailcore.Page')),
                ('date_from', models.DateField(null=True, verbose_name=b'Start date')),
                ('date_to', models.DateField(help_text=b'Not required if event is on a single day', null=True, verbose_name=b'End date', blank=True)),
                ('time_from', models.TimeField(null=True, verbose_name=b'Start time', blank=True)),
                ('time_to', models.TimeField(null=True, verbose_name=b'End time', blank=True)),
                ('audience', models.CharField(max_length=255, choices=[(b'public', b'Public'), (b'private', b'Private')])),
                ('location', models.CharField(max_length=255)),
                ('body', wagtail.wagtailcore.fields.RichTextField(blank=True)),
                ('cost', models.CharField(max_length=255)),
                ('signup_link', models.URLField(blank=True)),
                ('feed_image', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to_field='id', blank=True, to='wagtailimages.Image', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
    ]
