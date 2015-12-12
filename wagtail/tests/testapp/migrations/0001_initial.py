# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings
import modelcluster.contrib.taggit
import wagtail.wagtailimages.models
import wagtail.wagtailadmin.taggable
import modelcluster.fields
import wagtail.wagtailcore.fields
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0013_update_golive_expire_help_text'),
        ('wagtaildocs', '0002_initial_data'),
        ('taggit', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('wagtailimages', '0005_make_filter_spec_unique'),
    ]

    operations = [
        migrations.CreateModel(
            name='Advert',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('url', models.URLField(blank=True, null=True)),
                ('text', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AdvertPlacement',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('colour', models.CharField(max_length=255)),
                ('advert', models.ForeignKey(to='tests.Advert', related_name='+')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BusinessChild',
            fields=[
                (
                    'page_ptr',
                    models.OneToOneField(
                        parent_link=True,
                        primary_key=True,
                        to='wagtailcore.Page',
                        auto_created=True,
                        serialize=False
                    )
                ),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='BusinessIndex',
            fields=[
                (
                    'page_ptr',
                    models.OneToOneField(
                        parent_link=True,
                        primary_key=True,
                        to='wagtailcore.Page',
                        auto_created=True,
                        serialize=False
                    )
                ),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='BusinessSubIndex',
            fields=[
                (
                    'page_ptr',
                    models.OneToOneField(
                        parent_link=True,
                        primary_key=True,
                        to='wagtailcore.Page',
                        auto_created=True,
                        serialize=False
                    )
                ),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='CustomImageWithAdminFormFields',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('title', models.CharField(max_length=255, verbose_name='Title')),
                (
                    'file',
                    models.ImageField(
                        width_field='width',
                        height_field='height',
                        upload_to=wagtail.wagtailimages.models.get_upload_to,
                        verbose_name='File'
                    )
                ),
                ('width', models.IntegerField(editable=False)),
                ('height', models.IntegerField(editable=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('focal_point_x', models.PositiveIntegerField(blank=True, null=True)),
                ('focal_point_y', models.PositiveIntegerField(blank=True, null=True)),
                ('focal_point_width', models.PositiveIntegerField(blank=True, null=True)),
                ('focal_point_height', models.PositiveIntegerField(blank=True, null=True)),
                ('caption', models.CharField(max_length=255)),
                ('not_editable_field', models.CharField(max_length=255)),
                (
                    'tags',
                    taggit.managers.TaggableManager(
                        verbose_name='Tags',
                        to='taggit.Tag',
                        blank=True,
                        through='taggit.TaggedItem',
                        help_text=None
                    )
                ),
                (
                    'uploaded_by_user',
                    models.ForeignKey(null=True, blank=True, to=settings.AUTH_USER_MODEL, editable=False)
                ),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, wagtail.wagtailadmin.taggable.TagSearchable),
        ),
        migrations.CreateModel(
            name='CustomImageWithoutAdminFormFields',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('title', models.CharField(max_length=255, verbose_name='Title')),
                (
                    'file',
                    models.ImageField(
                        width_field='width',
                        height_field='height',
                        upload_to=wagtail.wagtailimages.models.get_upload_to,
                        verbose_name='File'
                    )
                ),
                ('width', models.IntegerField(editable=False)),
                ('height', models.IntegerField(editable=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('focal_point_x', models.PositiveIntegerField(blank=True, null=True)),
                ('focal_point_y', models.PositiveIntegerField(blank=True, null=True)),
                ('focal_point_width', models.PositiveIntegerField(blank=True, null=True)),
                ('focal_point_height', models.PositiveIntegerField(blank=True, null=True)),
                ('caption', models.CharField(max_length=255)),
                ('not_editable_field', models.CharField(max_length=255)),
                (
                    'tags',
                    taggit.managers.TaggableManager(
                        verbose_name='Tags',
                        to='taggit.Tag',
                        blank=True,
                        through='taggit.TaggedItem',
                        help_text=None
                    )
                ),
                (
                    'uploaded_by_user',
                    models.ForeignKey(null=True, blank=True, to=settings.AUTH_USER_MODEL, editable=False)
                ),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, wagtail.wagtailadmin.taggable.TagSearchable),
        ),
        migrations.CreateModel(
            name='EventIndex',
            fields=[
                (
                    'page_ptr',
                    models.OneToOneField(
                        parent_link=True,
                        primary_key=True,
                        to='wagtailcore.Page',
                        auto_created=True,
                        serialize=False
                    )
                ),
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
                (
                    'page_ptr',
                    models.OneToOneField(
                        parent_link=True,
                        primary_key=True,
                        to='wagtailcore.Page',
                        auto_created=True,
                        serialize=False
                    )
                ),
                ('date_from', models.DateField(verbose_name='Start date', null=True)),
                (
                    'date_to',
                    models.DateField(
                        blank=True,
                        help_text='Not required if event is on a single day',
                        verbose_name='End date',
                        null=True
                    )
                ),
                ('time_from', models.TimeField(blank=True, verbose_name='Start time', null=True)),
                ('time_to', models.TimeField(blank=True, verbose_name='End time', null=True)),
                ('audience', models.CharField(choices=[('public', 'Public'), ('private', 'Private')], max_length=255)),
                ('location', models.CharField(max_length=255)),
                ('body', wagtail.wagtailcore.fields.RichTextField(blank=True)),
                ('cost', models.CharField(max_length=255)),
                ('signup_link', models.URLField(blank=True)),
                ('feed_image',
                    models.ForeignKey(
                        to='wagtailimages.Image',
                        null=True,
                        related_name='+',
                        blank=True,
                        on_delete=django.db.models.deletion.SET_NULL
                    )),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='EventPageCarouselItem',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('sort_order', models.IntegerField(editable=False, null=True, blank=True)),
                ('link_external', models.URLField(blank=True, verbose_name='External link')),
                ('embed_url', models.URLField(blank=True, verbose_name='Embed URL')),
                ('caption', models.CharField(blank=True, max_length=255)),
                (
                    'image',
                    models.ForeignKey(
                        to='wagtailimages.Image',
                        null=True,
                        related_name='+',
                        blank=True,
                        on_delete=django.db.models.deletion.SET_NULL
                    )
                ),
                (
                    'link_document',
                    models.ForeignKey(to='wagtaildocs.Document', null=True, related_name='+', blank=True)
                ),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EventPageChooserModel',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('page', models.ForeignKey(to='tests.EventPage', help_text='more help text')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EventPageRelatedLink',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('sort_order', models.IntegerField(editable=False, null=True, blank=True)),
                ('link_external', models.URLField(blank=True, verbose_name='External link')),
                ('title', models.CharField(help_text='Link title', max_length=255)),
                (
                    'link_document',
                    models.ForeignKey(to='wagtaildocs.Document', null=True, related_name='+', blank=True)
                ),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EventPageSpeaker',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('sort_order', models.IntegerField(editable=False, null=True, blank=True)),
                ('link_external', models.URLField(blank=True, verbose_name='External link')),
                ('first_name', models.CharField(blank=True, max_length=255, verbose_name='Name')),
                ('last_name', models.CharField(blank=True, max_length=255, verbose_name='Surname')),
                (
                    'image',
                    models.ForeignKey(
                        to='wagtailimages.Image',
                        null=True,
                        related_name='+',
                        blank=True,
                        on_delete=django.db.models.deletion.SET_NULL
                    )
                ),
                (
                    'link_document',
                    models.ForeignKey(to='wagtaildocs.Document', null=True, related_name='+', blank=True)
                ),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FormField',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('sort_order', models.IntegerField(editable=False, null=True, blank=True)),
                ('label', models.CharField(help_text='The label of the form field', max_length=255)),
                (
                    'field_type',
                    models.CharField(
                        choices=[
                            ('singleline', 'Single line text'),
                            ('multiline', 'Multi-line text'),
                            ('email', 'Email'),
                            ('number', 'Number'),
                            ('url', 'URL'),
                            ('checkbox', 'Checkbox'),
                            ('checkboxes', 'Checkboxes'),
                            ('dropdown', 'Drop down'),
                            ('radio', 'Radio buttons'),
                            ('date', 'Date'),
                            ('datetime', 'Date/time')
                        ],
                        max_length=16
                    )
                ),
                ('required', models.BooleanField(default=True)),
                (
                    'choices',
                    models.CharField(
                        blank=True,
                        help_text='Comma separated list of choices. Only applicable in checkboxes, radio and dropdown.',
                        max_length=512
                    )
                ),
                (
                    'default_value',
                    models.CharField(
                        blank=True,
                        help_text='Default value. Comma separated values supported for checkboxes.',
                        max_length=255
                    )
                ),
                ('help_text', models.CharField(blank=True, max_length=255)),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FormPage',
            fields=[
                (
                    'page_ptr',
                    models.OneToOneField(
                        parent_link=True,
                        primary_key=True,
                        to='wagtailcore.Page',
                        auto_created=True,
                        serialize=False
                    )
                ),
                (
                    'to_address',
                    models.CharField(
                        blank=True,
                        help_text='Optional - form submissions will be emailed to this address',
                        max_length=255
                    )
                ),
                ('from_address', models.CharField(blank=True, max_length=255)),
                ('subject', models.CharField(blank=True, max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='PageChooserModel',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PageWithOldStyleRouteMethod',
            fields=[
                (
                    'page_ptr',
                    models.OneToOneField(
                        parent_link=True,
                        primary_key=True,
                        to='wagtailcore.Page',
                        auto_created=True,
                        serialize=False
                    )
                ),
                ('content', models.TextField()),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='SimplePage',
            fields=[
                (
                    'page_ptr',
                    models.OneToOneField(
                        parent_link=True,
                        primary_key=True,
                        to='wagtailcore.Page',
                        auto_created=True,
                        serialize=False
                    )
                ),
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
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('advert', models.ForeignKey(to='tests.Advert', help_text='help text')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StandardChild',
            fields=[
                (
                    'page_ptr',
                    models.OneToOneField(
                        parent_link=True,
                        primary_key=True,
                        to='wagtailcore.Page',
                        auto_created=True,
                        serialize=False
                    )
                ),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='StandardIndex',
            fields=[
                (
                    'page_ptr',
                    models.OneToOneField(
                        parent_link=True,
                        primary_key=True,
                        to='wagtailcore.Page',
                        auto_created=True,
                        serialize=False
                    )
                ),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='TaggedPage',
            fields=[
                (
                    'page_ptr',
                    models.OneToOneField(
                        parent_link=True,
                        primary_key=True,
                        to='wagtailcore.Page',
                        auto_created=True,
                        serialize=False
                    )
                ),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='TaggedPageTag',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('content_object', modelcluster.fields.ParentalKey(to='tests.TaggedPage', related_name='tagged_items')),
                ('tag', models.ForeignKey(to='taggit.Tag', related_name='tests_taggedpagetag_items')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='taggedpage',
            name='tags',
            field=modelcluster.contrib.taggit.ClusterTaggableManager(
                verbose_name='Tags',
                to='taggit.Tag',
                blank=True,
                through='tests.TaggedPageTag',
                help_text='A comma-separated list of tags.'
            ),
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
            field=models.ForeignKey(to='wagtailcore.Page', null=True, related_name='+', blank=True),
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
            field=models.ForeignKey(to='wagtailcore.Page', null=True, related_name='+', blank=True),
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
            field=models.ForeignKey(to='wagtailcore.Page', null=True, related_name='+', blank=True),
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
    ]
