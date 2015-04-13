# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import modelcluster.tags
import django.db.models.deletion
import wagtail.wagtailcore.fields
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0013_update_golive_expire_help_text'),
        ('wagtailimages', '0005_make_filter_spec_unique'),
        ('taggit', '0001_initial'),
        ('wagtaildocs', '0002_initial_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='BlogEntryPage',
            fields=[
                ('page_ptr', models.OneToOneField(primary_key=True, related_name='+', to='wagtailcore.Page', serialize=False, parent_link=True)),
                ('body', wagtail.wagtailcore.fields.RichTextField()),
                ('date', models.DateField(verbose_name='Post date')),
                ('feed_image', models.ForeignKey(null=True, related_name='+', blank=True, to='wagtailimages.Image', on_delete=django.db.models.deletion.SET_NULL)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='BlogEntryPageCarouselItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('link_external', models.URLField(verbose_name='External link', blank=True)),
                ('embed_url', models.URLField(verbose_name='Embed URL', blank=True)),
                ('caption', models.CharField(max_length=255, blank=True)),
                ('image', models.ForeignKey(null=True, related_name='+', blank=True, to='wagtailimages.Image', on_delete=django.db.models.deletion.SET_NULL)),
                ('link_document', models.ForeignKey(null=True, related_name='+', blank=True, to='wagtaildocs.Document')),
            ],
            options={
                'abstract': False,
                'ordering': ['sort_order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BlogEntryPageRelatedLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('link_external', models.URLField(verbose_name='External link', blank=True)),
                ('title', models.CharField(max_length=255, help_text='Link title')),
                ('link_document', models.ForeignKey(null=True, related_name='+', blank=True, to='wagtaildocs.Document')),
            ],
            options={
                'abstract': False,
                'ordering': ['sort_order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BlogEntryPageTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content_object', modelcluster.fields.ParentalKey(to='demosite.BlogEntryPage', related_name='tagged_items')),
                ('tag', models.ForeignKey(to='taggit.Tag', related_name='demosite_blogentrypagetag_items')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BlogIndexPage',
            fields=[
                ('page_ptr', models.OneToOneField(primary_key=True, related_name='+', to='wagtailcore.Page', serialize=False, parent_link=True)),
                ('intro', wagtail.wagtailcore.fields.RichTextField(blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='BlogIndexPageRelatedLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('link_external', models.URLField(verbose_name='External link', blank=True)),
                ('title', models.CharField(max_length=255, help_text='Link title')),
                ('link_document', models.ForeignKey(null=True, related_name='+', blank=True, to='wagtaildocs.Document')),
            ],
            options={
                'abstract': False,
                'ordering': ['sort_order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ContactPage',
            fields=[
                ('telephone', models.CharField(max_length=20, blank=True)),
                ('email', models.EmailField(max_length=254, blank=True)),
                ('address_1', models.CharField(max_length=255, blank=True)),
                ('address_2', models.CharField(max_length=255, blank=True)),
                ('city', models.CharField(max_length=255, blank=True)),
                ('country', models.CharField(max_length=255, blank=True)),
                ('post_code', models.CharField(max_length=10, blank=True)),
                ('page_ptr', models.OneToOneField(primary_key=True, related_name='+', to='wagtailcore.Page', serialize=False, parent_link=True)),
                ('body', wagtail.wagtailcore.fields.RichTextField(blank=True)),
                ('feed_image', models.ForeignKey(null=True, related_name='+', blank=True, to='wagtailimages.Image', on_delete=django.db.models.deletion.SET_NULL)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page', models.Model),
        ),
        migrations.CreateModel(
            name='EventIndexPage',
            fields=[
                ('page_ptr', models.OneToOneField(primary_key=True, related_name='+', to='wagtailcore.Page', serialize=False, parent_link=True)),
                ('intro', wagtail.wagtailcore.fields.RichTextField(blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='EventIndexPageRelatedLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('link_external', models.URLField(verbose_name='External link', blank=True)),
                ('title', models.CharField(max_length=255, help_text='Link title')),
                ('link_document', models.ForeignKey(null=True, related_name='+', blank=True, to='wagtaildocs.Document')),
            ],
            options={
                'abstract': False,
                'ordering': ['sort_order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EventPage',
            fields=[
                ('page_ptr', models.OneToOneField(primary_key=True, related_name='+', to='wagtailcore.Page', serialize=False, parent_link=True)),
                ('date_from', models.DateField(verbose_name='Start date')),
                ('date_to', models.DateField(null=True, help_text='Not required if event is on a single day', verbose_name='End date', blank=True)),
                ('time_from', models.TimeField(null=True, verbose_name='Start time', blank=True)),
                ('time_to', models.TimeField(null=True, verbose_name='End time', blank=True)),
                ('audience', models.CharField(choices=[('public', 'Public'), ('private', 'Private')], max_length=255)),
                ('location', models.CharField(max_length=255)),
                ('body', wagtail.wagtailcore.fields.RichTextField(blank=True)),
                ('cost', models.CharField(max_length=255)),
                ('signup_link', models.URLField(blank=True)),
                ('feed_image', models.ForeignKey(null=True, related_name='+', blank=True, to='wagtailimages.Image', on_delete=django.db.models.deletion.SET_NULL)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='EventPageCarouselItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('link_external', models.URLField(verbose_name='External link', blank=True)),
                ('embed_url', models.URLField(verbose_name='Embed URL', blank=True)),
                ('caption', models.CharField(max_length=255, blank=True)),
                ('image', models.ForeignKey(null=True, related_name='+', blank=True, to='wagtailimages.Image', on_delete=django.db.models.deletion.SET_NULL)),
                ('link_document', models.ForeignKey(null=True, related_name='+', blank=True, to='wagtaildocs.Document')),
            ],
            options={
                'abstract': False,
                'ordering': ['sort_order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EventPageRelatedLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('link_external', models.URLField(verbose_name='External link', blank=True)),
                ('title', models.CharField(max_length=255, help_text='Link title')),
                ('link_document', models.ForeignKey(null=True, related_name='+', blank=True, to='wagtaildocs.Document')),
            ],
            options={
                'abstract': False,
                'ordering': ['sort_order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EventPageSpeaker',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('link_external', models.URLField(verbose_name='External link', blank=True)),
                ('first_name', models.CharField(max_length=255, verbose_name='Name', blank=True)),
                ('last_name', models.CharField(max_length=255, verbose_name='Surname', blank=True)),
                ('image', models.ForeignKey(null=True, related_name='+', blank=True, to='wagtailimages.Image', on_delete=django.db.models.deletion.SET_NULL)),
                ('link_document', models.ForeignKey(null=True, related_name='+', blank=True, to='wagtaildocs.Document')),
            ],
            options={
                'abstract': False,
                'ordering': ['sort_order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HomePage',
            fields=[
                ('page_ptr', models.OneToOneField(primary_key=True, related_name='+', to='wagtailcore.Page', serialize=False, parent_link=True)),
                ('body', wagtail.wagtailcore.fields.RichTextField(blank=True)),
            ],
            options={
                'verbose_name': 'Homepage',
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='HomePageCarouselItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('link_external', models.URLField(verbose_name='External link', blank=True)),
                ('embed_url', models.URLField(verbose_name='Embed URL', blank=True)),
                ('caption', models.CharField(max_length=255, blank=True)),
                ('image', models.ForeignKey(null=True, related_name='+', blank=True, to='wagtailimages.Image', on_delete=django.db.models.deletion.SET_NULL)),
                ('link_document', models.ForeignKey(null=True, related_name='+', blank=True, to='wagtaildocs.Document')),
            ],
            options={
                'abstract': False,
                'ordering': ['sort_order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HomePageRelatedLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('link_external', models.URLField(verbose_name='External link', blank=True)),
                ('title', models.CharField(max_length=255, help_text='Link title')),
                ('link_document', models.ForeignKey(null=True, related_name='+', blank=True, to='wagtaildocs.Document')),
            ],
            options={
                'abstract': False,
                'ordering': ['sort_order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PersonPage',
            fields=[
                ('telephone', models.CharField(max_length=20, blank=True)),
                ('email', models.EmailField(max_length=254, blank=True)),
                ('address_1', models.CharField(max_length=255, blank=True)),
                ('address_2', models.CharField(max_length=255, blank=True)),
                ('city', models.CharField(max_length=255, blank=True)),
                ('country', models.CharField(max_length=255, blank=True)),
                ('post_code', models.CharField(max_length=10, blank=True)),
                ('page_ptr', models.OneToOneField(primary_key=True, related_name='+', to='wagtailcore.Page', serialize=False, parent_link=True)),
                ('first_name', models.CharField(max_length=255)),
                ('last_name', models.CharField(max_length=255)),
                ('intro', wagtail.wagtailcore.fields.RichTextField(blank=True)),
                ('biography', wagtail.wagtailcore.fields.RichTextField(blank=True)),
                ('feed_image', models.ForeignKey(null=True, related_name='+', blank=True, to='wagtailimages.Image', on_delete=django.db.models.deletion.SET_NULL)),
                ('image', models.ForeignKey(null=True, related_name='+', blank=True, to='wagtailimages.Image', on_delete=django.db.models.deletion.SET_NULL)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page', models.Model),
        ),
        migrations.CreateModel(
            name='PersonPageRelatedLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('link_external', models.URLField(verbose_name='External link', blank=True)),
                ('title', models.CharField(max_length=255, help_text='Link title')),
                ('link_document', models.ForeignKey(null=True, related_name='+', blank=True, to='wagtaildocs.Document')),
            ],
            options={
                'abstract': False,
                'ordering': ['sort_order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StandardIndexPage',
            fields=[
                ('page_ptr', models.OneToOneField(primary_key=True, related_name='+', to='wagtailcore.Page', serialize=False, parent_link=True)),
                ('intro', wagtail.wagtailcore.fields.RichTextField(blank=True)),
                ('feed_image', models.ForeignKey(null=True, related_name='+', blank=True, to='wagtailimages.Image', on_delete=django.db.models.deletion.SET_NULL)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='StandardIndexPageRelatedLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('link_external', models.URLField(verbose_name='External link', blank=True)),
                ('title', models.CharField(max_length=255, help_text='Link title')),
                ('link_document', models.ForeignKey(null=True, related_name='+', blank=True, to='wagtaildocs.Document')),
            ],
            options={
                'abstract': False,
                'ordering': ['sort_order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StandardPage',
            fields=[
                ('page_ptr', models.OneToOneField(primary_key=True, related_name='+', to='wagtailcore.Page', serialize=False, parent_link=True)),
                ('intro', wagtail.wagtailcore.fields.RichTextField(blank=True)),
                ('body', wagtail.wagtailcore.fields.RichTextField(blank=True)),
                ('feed_image', models.ForeignKey(null=True, related_name='+', blank=True, to='wagtailimages.Image', on_delete=django.db.models.deletion.SET_NULL)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='StandardPageCarouselItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('link_external', models.URLField(verbose_name='External link', blank=True)),
                ('embed_url', models.URLField(verbose_name='Embed URL', blank=True)),
                ('caption', models.CharField(max_length=255, blank=True)),
                ('image', models.ForeignKey(null=True, related_name='+', blank=True, to='wagtailimages.Image', on_delete=django.db.models.deletion.SET_NULL)),
                ('link_document', models.ForeignKey(null=True, related_name='+', blank=True, to='wagtaildocs.Document')),
                ('link_page', models.ForeignKey(null=True, related_name='+', blank=True, to='wagtailcore.Page')),
                ('page', modelcluster.fields.ParentalKey(to='demosite.StandardPage', related_name='carousel_items')),
            ],
            options={
                'abstract': False,
                'ordering': ['sort_order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StandardPageRelatedLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('link_external', models.URLField(verbose_name='External link', blank=True)),
                ('title', models.CharField(max_length=255, help_text='Link title')),
                ('link_document', models.ForeignKey(null=True, related_name='+', blank=True, to='wagtaildocs.Document')),
                ('link_page', models.ForeignKey(null=True, related_name='+', blank=True, to='wagtailcore.Page')),
                ('page', modelcluster.fields.ParentalKey(to='demosite.StandardPage', related_name='related_links')),
            ],
            options={
                'abstract': False,
                'ordering': ['sort_order'],
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='standardindexpagerelatedlink',
            name='link_page',
            field=models.ForeignKey(null=True, related_name='+', blank=True, to='wagtailcore.Page'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='standardindexpagerelatedlink',
            name='page',
            field=modelcluster.fields.ParentalKey(to='demosite.StandardIndexPage', related_name='related_links'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='personpagerelatedlink',
            name='link_page',
            field=models.ForeignKey(null=True, related_name='+', blank=True, to='wagtailcore.Page'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='personpagerelatedlink',
            name='page',
            field=modelcluster.fields.ParentalKey(to='demosite.PersonPage', related_name='related_links'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='homepagerelatedlink',
            name='link_page',
            field=models.ForeignKey(null=True, related_name='+', blank=True, to='wagtailcore.Page'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='homepagerelatedlink',
            name='page',
            field=modelcluster.fields.ParentalKey(to='demosite.HomePage', related_name='related_links'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='homepagecarouselitem',
            name='link_page',
            field=models.ForeignKey(null=True, related_name='+', blank=True, to='wagtailcore.Page'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='homepagecarouselitem',
            name='page',
            field=modelcluster.fields.ParentalKey(to='demosite.HomePage', related_name='carousel_items'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventpagespeaker',
            name='link_page',
            field=models.ForeignKey(null=True, related_name='+', blank=True, to='wagtailcore.Page'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventpagespeaker',
            name='page',
            field=modelcluster.fields.ParentalKey(to='demosite.EventPage', related_name='speakers'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventpagerelatedlink',
            name='link_page',
            field=models.ForeignKey(null=True, related_name='+', blank=True, to='wagtailcore.Page'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventpagerelatedlink',
            name='page',
            field=modelcluster.fields.ParentalKey(to='demosite.EventPage', related_name='related_links'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventpagecarouselitem',
            name='link_page',
            field=models.ForeignKey(null=True, related_name='+', blank=True, to='wagtailcore.Page'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventpagecarouselitem',
            name='page',
            field=modelcluster.fields.ParentalKey(to='demosite.EventPage', related_name='carousel_items'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventindexpagerelatedlink',
            name='link_page',
            field=models.ForeignKey(null=True, related_name='+', blank=True, to='wagtailcore.Page'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventindexpagerelatedlink',
            name='page',
            field=modelcluster.fields.ParentalKey(to='demosite.EventIndexPage', related_name='related_links'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='blogindexpagerelatedlink',
            name='link_page',
            field=models.ForeignKey(null=True, related_name='+', blank=True, to='wagtailcore.Page'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='blogindexpagerelatedlink',
            name='page',
            field=modelcluster.fields.ParentalKey(to='demosite.BlogIndexPage', related_name='related_links'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='blogentrypagerelatedlink',
            name='link_page',
            field=models.ForeignKey(null=True, related_name='+', blank=True, to='wagtailcore.Page'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='blogentrypagerelatedlink',
            name='page',
            field=modelcluster.fields.ParentalKey(to='demosite.BlogEntryPage', related_name='related_links'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='blogentrypagecarouselitem',
            name='link_page',
            field=models.ForeignKey(null=True, related_name='+', blank=True, to='wagtailcore.Page'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='blogentrypagecarouselitem',
            name='page',
            field=modelcluster.fields.ParentalKey(to='demosite.BlogEntryPage', related_name='carousel_items'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='blogentrypage',
            name='tags',
            field=modelcluster.tags.ClusterTaggableManager(through='demosite.BlogEntryPageTag', blank=True, to='taggit.Tag', help_text='A comma-separated list of tags.', verbose_name='Tags'),
            preserve_default=True,
        ),
    ]
