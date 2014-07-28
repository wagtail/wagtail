# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import taggit.models
import wagtail.wagtailsearch.indexed
import modelcluster.fields
import wagtail.wagtailcore.fields
import modelcluster.tags
import wagtail.tests.models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0002_initial_data'),
        ('wagtaildocs', '0002_initial_data'),
        ('wagtailimages', '0002_initial_data'),
        ('taggit', '0001_initial'),
        ('tests', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Advert',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(null=True, blank=True)),
                ('text', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AlphaSnippet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BusinessChild',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='BusinessIndex',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='BusinessSubIndex',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='EventIndex',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
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
                ('page_ptr', models.OneToOneField(auto_created=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('date_from', models.DateField(null=True, verbose_name=b'Start date')),
                ('date_to', models.DateField(help_text=b'Not required if event is on a single day', null=True, verbose_name=b'End date', blank=True)),
                ('time_from', models.TimeField(null=True, verbose_name=b'Start time', blank=True)),
                ('time_to', models.TimeField(null=True, verbose_name=b'End time', blank=True)),
                ('audience', models.CharField(max_length=255, choices=[(b'public', b'Public'), (b'private', b'Private')])),
                ('location', models.CharField(max_length=255)),
                ('body', wagtail.wagtailcore.fields.RichTextField(blank=True)),
                ('cost', models.CharField(max_length=255)),
                ('signup_link', models.URLField(blank=True)),
                ('feed_image', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='wagtailimages.Image', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='EventPageCarouselItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('link_external', models.URLField(verbose_name=b'External link', blank=True)),
                ('embed_url', models.URLField(verbose_name=b'Embed URL', blank=True)),
                ('caption', models.CharField(max_length=255, blank=True)),
                ('image', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='wagtailimages.Image', null=True)),
                ('link_document', models.ForeignKey(blank=True, to='wagtaildocs.Document', null=True)),
                ('link_page', models.ForeignKey(blank=True, to='wagtailcore.Page', null=True)),
                ('page', modelcluster.fields.ParentalKey(to='tests.EventPage')),
            ],
            options={
                'ordering': [b'sort_order'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EventPageRelatedLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('link_external', models.URLField(verbose_name=b'External link', blank=True)),
                ('title', models.CharField(help_text=b'Link title', max_length=255)),
                ('link_document', models.ForeignKey(blank=True, to='wagtaildocs.Document', null=True)),
                ('link_page', models.ForeignKey(blank=True, to='wagtailcore.Page', null=True)),
                ('page', modelcluster.fields.ParentalKey(to='tests.EventPage')),
            ],
            options={
                'ordering': [b'sort_order'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EventPageSpeaker',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('link_external', models.URLField(verbose_name=b'External link', blank=True)),
                ('first_name', models.CharField(max_length=255, verbose_name=b'Name', blank=True)),
                ('last_name', models.CharField(max_length=255, verbose_name=b'Surname', blank=True)),
                ('image', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='wagtailimages.Image', null=True)),
                ('link_document', models.ForeignKey(blank=True, to='wagtaildocs.Document', null=True)),
                ('link_page', models.ForeignKey(blank=True, to='wagtailcore.Page', null=True)),
                ('page', modelcluster.fields.ParentalKey(to='tests.EventPage')),
            ],
            options={
                'ordering': [b'sort_order'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FormField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('label', models.CharField(help_text='The label of the form field', max_length=255)),
                ('field_type', models.CharField(max_length=16, choices=[(b'singleline', 'Single line text'), (b'multiline', 'Multi-line text'), (b'email', 'Email'), (b'number', 'Number'), (b'url', 'URL'), (b'checkbox', 'Checkbox'), (b'checkboxes', 'Checkboxes'), (b'dropdown', 'Drop down'), (b'radio', 'Radio buttons'), (b'date', 'Date'), (b'datetime', 'Date/time')])),
                ('required', models.BooleanField(default=True)),
                ('choices', models.CharField(help_text='Comma seperated list of choices. Only applicable in checkboxes, radio and dropdown.', max_length=512, blank=True)),
                ('default_value', models.CharField(help_text='Default value. Comma seperated values supported for checkboxes.', max_length=255, blank=True)),
                ('help_text', models.CharField(max_length=255, blank=True)),
            ],
            options={
                'ordering': [b'sort_order'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FormPage',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('to_address', models.CharField(help_text='Optional - form submissions will be emailed to this address', max_length=255, blank=True)),
                ('from_address', models.CharField(max_length=255, blank=True)),
                ('subject', models.CharField(max_length=255, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.AddField(
            model_name='formfield',
            name='page',
            field=modelcluster.fields.ParentalKey(to='tests.FormPage'),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='PageWithOldStyleRouteMethod',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('content', models.TextField()),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='RoutablePageTest',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='SearchTest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('content', models.TextField()),
                ('live', models.BooleanField(default=False)),
                ('published_date', models.DateField(null=True)),
            ],
            options={
            },
            bases=(models.Model, wagtail.wagtailsearch.indexed.Indexed),
        ),
        migrations.CreateModel(
            name='SearchTestChild',
            fields=[
                ('searchtest_ptr', models.OneToOneField(auto_created=True, primary_key=True, serialize=False, to='tests.SearchTest')),
                ('subtitle', models.CharField(max_length=255, null=True, blank=True)),
                ('extra_content', models.TextField()),
            ],
            options={
            },
            bases=('tests.searchtest',),
        ),
        migrations.CreateModel(
            name='SearchTestOldConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model, wagtail.wagtailsearch.indexed.Indexed),
        ),
        migrations.CreateModel(
            name='SearchTestOldConfigList',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model, wagtail.wagtailsearch.indexed.Indexed),
        ),
        migrations.CreateModel(
            name='SimplePage',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('content', models.TextField()),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='StandardChild',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='StandardIndex',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='TaggedPage',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='TaggedPageTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='taggedpage',
            name='tags',
            field=modelcluster.tags.ClusterTaggableManager(to=taggit.models.Tag, through=wagtail.tests.models.TaggedPageTag, blank=True, help_text='A comma-separated list of tags.', verbose_name='Tags'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taggedpagetag',
            name='content_object',
            field=modelcluster.fields.ParentalKey(to='tests.TaggedPage'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taggedpagetag',
            name='tag',
            field=models.ForeignKey(to='taggit.Tag'),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='ZuluSnippet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
