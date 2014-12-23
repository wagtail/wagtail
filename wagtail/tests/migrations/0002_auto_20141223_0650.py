# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import wagtail.wagtailsearch.index
import wagtail.wagtailcore.fields
import django.db.models.deletion
import wagtail.contrib.wagtailroutablepage.models
import modelcluster.fields
import modelcluster.tags


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0005_make_filter_spec_unique'),
        ('wagtailcore', '0010_change_page_owner_to_null_on_delete'),
        ('taggit', '0001_initial'),
        ('wagtaildocs', '0002_initial_data'),
        ('tests', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Advert',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('url', models.URLField(null=True, blank=True)),
                ('text', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AdvertPlacement',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('colour', models.CharField(max_length=255)),
                ('advert', models.ForeignKey(to='tests.Advert', related_name='+')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AlphaSnippet',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('text', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BusinessChild',
            fields=[
                ('page_ptr', models.OneToOneField(to='wagtailcore.Page', auto_created=True, primary_key=True, parent_link=True, serialize=False)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='BusinessIndex',
            fields=[
                ('page_ptr', models.OneToOneField(to='wagtailcore.Page', auto_created=True, primary_key=True, parent_link=True, serialize=False)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='BusinessSubIndex',
            fields=[
                ('page_ptr', models.OneToOneField(to='wagtailcore.Page', auto_created=True, primary_key=True, parent_link=True, serialize=False)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='EventIndex',
            fields=[
                ('page_ptr', models.OneToOneField(to='wagtailcore.Page', auto_created=True, primary_key=True, parent_link=True, serialize=False)),
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
                ('page_ptr', models.OneToOneField(to='wagtailcore.Page', auto_created=True, primary_key=True, parent_link=True, serialize=False)),
                ('date_from', models.DateField(null=True, verbose_name='Start date')),
                ('date_to', models.DateField(null=True, blank=True, verbose_name='End date', help_text='Not required if event is on a single day')),
                ('time_from', models.TimeField(null=True, blank=True, verbose_name='Start time')),
                ('time_to', models.TimeField(null=True, blank=True, verbose_name='End time')),
                ('audience', models.CharField(choices=[('public', 'Public'), ('private', 'Private')], max_length=255)),
                ('location', models.CharField(max_length=255)),
                ('body', wagtail.wagtailcore.fields.RichTextField(blank=True)),
                ('cost', models.CharField(max_length=255)),
                ('signup_link', models.URLField(blank=True)),
                ('feed_image', models.ForeignKey(to='wagtailimages.Image', null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, related_name='+')),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='EventPageCarouselItem',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('sort_order', models.IntegerField(null=True, blank=True, editable=False)),
                ('link_external', models.URLField(blank=True, verbose_name='External link')),
                ('embed_url', models.URLField(blank=True, verbose_name='Embed URL')),
                ('caption', models.CharField(max_length=255, blank=True)),
                ('image', models.ForeignKey(to='wagtailimages.Image', null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, related_name='+')),
                ('link_document', models.ForeignKey(to='wagtaildocs.Document', null=True, blank=True, related_name='+')),
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
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('sort_order', models.IntegerField(null=True, blank=True, editable=False)),
                ('link_external', models.URLField(blank=True, verbose_name='External link')),
                ('title', models.CharField(max_length=255, help_text='Link title')),
                ('link_document', models.ForeignKey(to='wagtaildocs.Document', null=True, blank=True, related_name='+')),
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
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('sort_order', models.IntegerField(null=True, blank=True, editable=False)),
                ('link_external', models.URLField(blank=True, verbose_name='External link')),
                ('first_name', models.CharField(max_length=255, blank=True, verbose_name='Name')),
                ('last_name', models.CharField(max_length=255, blank=True, verbose_name='Surname')),
                ('image', models.ForeignKey(to='wagtailimages.Image', null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, related_name='+')),
                ('link_document', models.ForeignKey(to='wagtaildocs.Document', null=True, blank=True, related_name='+')),
            ],
            options={
                'abstract': False,
                'ordering': ['sort_order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FormField',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('sort_order', models.IntegerField(null=True, blank=True, editable=False)),
                ('label', models.CharField(max_length=255, help_text='The label of the form field')),
                ('field_type', models.CharField(choices=[('singleline', 'Single line text'), ('multiline', 'Multi-line text'), ('email', 'Email'), ('number', 'Number'), ('url', 'URL'), ('checkbox', 'Checkbox'), ('checkboxes', 'Checkboxes'), ('dropdown', 'Drop down'), ('radio', 'Radio buttons'), ('date', 'Date'), ('datetime', 'Date/time')], max_length=16)),
                ('required', models.BooleanField(default=True)),
                ('choices', models.CharField(max_length=512, blank=True, help_text='Comma separated list of choices. Only applicable in checkboxes, radio and dropdown.')),
                ('default_value', models.CharField(max_length=255, blank=True, help_text='Default value. Comma separated values supported for checkboxes.')),
                ('help_text', models.CharField(max_length=255, blank=True)),
            ],
            options={
                'abstract': False,
                'ordering': ['sort_order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FormPage',
            fields=[
                ('page_ptr', models.OneToOneField(to='wagtailcore.Page', auto_created=True, primary_key=True, parent_link=True, serialize=False)),
                ('to_address', models.CharField(max_length=255, blank=True, help_text='Optional - form submissions will be emailed to this address')),
                ('from_address', models.CharField(max_length=255, blank=True)),
                ('subject', models.CharField(max_length=255, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='PageChooserModel',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PageWithOldStyleRouteMethod',
            fields=[
                ('page_ptr', models.OneToOneField(to='wagtailcore.Page', auto_created=True, primary_key=True, parent_link=True, serialize=False)),
                ('content', models.TextField()),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='RegisterDecorator',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RegisterFunction',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RoutablePageTest',
            fields=[
                ('page_ptr', models.OneToOneField(to='wagtailcore.Page', auto_created=True, primary_key=True, parent_link=True, serialize=False)),
            ],
            options={
                'abstract': False,
            },
            bases=(wagtail.contrib.wagtailroutablepage.models.RoutablePageMixin, 'wagtailcore.page'),
        ),
        migrations.CreateModel(
            name='SearchTest',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('title', models.CharField(max_length=255)),
                ('content', models.TextField()),
                ('live', models.BooleanField(default=False)),
                ('published_date', models.DateField(null=True)),
            ],
            options={
            },
            bases=(models.Model, wagtail.wagtailsearch.index.Indexed),
        ),
        migrations.CreateModel(
            name='SearchTestChild',
            fields=[
                ('searchtest_ptr', models.OneToOneField(to='tests.SearchTest', auto_created=True, primary_key=True, parent_link=True, serialize=False)),
                ('subtitle', models.CharField(null=True, max_length=255, blank=True)),
                ('extra_content', models.TextField()),
            ],
            options={
            },
            bases=('tests.searchtest',),
        ),
        migrations.CreateModel(
            name='SimplePage',
            fields=[
                ('page_ptr', models.OneToOneField(to='wagtailcore.Page', auto_created=True, primary_key=True, parent_link=True, serialize=False)),
                ('content', models.TextField()),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='SnippetChooserModel',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('advert', models.ForeignKey(to='tests.Advert', help_text='help text')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StandardChild',
            fields=[
                ('page_ptr', models.OneToOneField(to='wagtailcore.Page', auto_created=True, primary_key=True, parent_link=True, serialize=False)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='StandardIndex',
            fields=[
                ('page_ptr', models.OneToOneField(to='wagtailcore.Page', auto_created=True, primary_key=True, parent_link=True, serialize=False)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='TaggedPage',
            fields=[
                ('page_ptr', models.OneToOneField(to='wagtailcore.Page', auto_created=True, primary_key=True, parent_link=True, serialize=False)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='TaggedPageTag',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('content_object', modelcluster.fields.ParentalKey(to='tests.TaggedPage', related_name='tagged_items')),
                ('tag', models.ForeignKey(to='taggit.Tag', related_name='tests_taggedpagetag_items')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ZuluSnippet',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('text', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='taggedpage',
            name='tags',
            field=modelcluster.tags.ClusterTaggableManager(blank=True, verbose_name='Tags', help_text='A comma-separated list of tags.', to='taggit.Tag', through='tests.TaggedPageTag'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='pagechoosermodel',
            name='page',
            field=models.ForeignKey(to='wagtailcore.Page', help_text='help text'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='formfield',
            name='page',
            field=modelcluster.fields.ParentalKey(to='tests.FormPage', related_name='form_fields'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventpagespeaker',
            name='link_page',
            field=models.ForeignKey(to='wagtailcore.Page', null=True, blank=True, related_name='+'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventpagespeaker',
            name='page',
            field=modelcluster.fields.ParentalKey(to='tests.EventPage', related_name='speakers'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventpagerelatedlink',
            name='link_page',
            field=models.ForeignKey(to='wagtailcore.Page', null=True, blank=True, related_name='+'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventpagerelatedlink',
            name='page',
            field=modelcluster.fields.ParentalKey(to='tests.EventPage', related_name='related_links'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventpagecarouselitem',
            name='link_page',
            field=models.ForeignKey(to='wagtailcore.Page', null=True, blank=True, related_name='+'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventpagecarouselitem',
            name='page',
            field=modelcluster.fields.ParentalKey(to='tests.EventPage', related_name='carousel_items'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='advertplacement',
            name='page',
            field=modelcluster.fields.ParentalKey(to='wagtailcore.Page', related_name='advert_placements'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='customuser',
            name='groups',
            field=models.ManyToManyField(related_name='user_set', blank=True, verbose_name='groups', help_text='The groups this user belongs to. A user will get all permissions granted to each of his/her group.', to='auth.Group', related_query_name='user'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='customuser',
            name='user_permissions',
            field=models.ManyToManyField(related_name='user_set', blank=True, verbose_name='user permissions', help_text='Specific permissions for this user.', to='auth.Permission', related_query_name='user'),
            preserve_default=True,
        ),
    ]
