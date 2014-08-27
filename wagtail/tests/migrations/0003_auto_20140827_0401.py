# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import modelcluster.fields
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0002_initial_data'),
        ('tests', '0002_auto_20140728_1636'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdvertPlacement',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('advert', models.ForeignKey(to='tests.Advert', related_name='+')),
                ('page', modelcluster.fields.ParentalKey(to='wagtailcore.Page', related_name='advert_placements')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterModelOptions(
            name='eventpagecarouselitem',
            options={'ordering': ['sort_order']},
        ),
        migrations.AlterModelOptions(
            name='eventpagerelatedlink',
            options={'ordering': ['sort_order']},
        ),
        migrations.AlterModelOptions(
            name='eventpagespeaker',
            options={'ordering': ['sort_order']},
        ),
        migrations.AlterModelOptions(
            name='formfield',
            options={'ordering': ['sort_order']},
        ),
        migrations.AlterField(
            model_name='businesschild',
            name='page_ptr',
            field=models.OneToOneField(serialize=False, to='wagtailcore.Page', parent_link=True, auto_created=True, primary_key=True),
        ),
        migrations.AlterField(
            model_name='businessindex',
            name='page_ptr',
            field=models.OneToOneField(serialize=False, to='wagtailcore.Page', parent_link=True, auto_created=True, primary_key=True),
        ),
        migrations.AlterField(
            model_name='businesssubindex',
            name='page_ptr',
            field=models.OneToOneField(serialize=False, to='wagtailcore.Page', parent_link=True, auto_created=True, primary_key=True),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='groups',
            field=models.ManyToManyField(help_text='The groups this user belongs to. A user will get all permissions granted to each of his/her group.', to='auth.Group', related_name='user_set', related_query_name='user', blank=True, verbose_name='groups'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='user_permissions',
            field=models.ManyToManyField(help_text='Specific permissions for this user.', to='auth.Permission', related_name='user_set', related_query_name='user', blank=True, verbose_name='user permissions'),
        ),
        migrations.AlterField(
            model_name='eventindex',
            name='page_ptr',
            field=models.OneToOneField(serialize=False, to='wagtailcore.Page', parent_link=True, auto_created=True, primary_key=True),
        ),
        migrations.AlterField(
            model_name='eventpage',
            name='audience',
            field=models.CharField(choices=[('public', 'Public'), ('private', 'Private')], max_length=255),
        ),
        migrations.AlterField(
            model_name='eventpage',
            name='date_from',
            field=models.DateField(verbose_name='Start date', null=True),
        ),
        migrations.AlterField(
            model_name='eventpage',
            name='date_to',
            field=models.DateField(help_text='Not required if event is on a single day', verbose_name='End date', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='eventpage',
            name='feed_image',
            field=models.ForeignKey(to='wagtailimages.Image', on_delete=django.db.models.deletion.SET_NULL, related_name='+', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='eventpage',
            name='page_ptr',
            field=models.OneToOneField(serialize=False, to='wagtailcore.Page', parent_link=True, auto_created=True, primary_key=True),
        ),
        migrations.AlterField(
            model_name='eventpage',
            name='time_from',
            field=models.TimeField(verbose_name='Start time', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='eventpage',
            name='time_to',
            field=models.TimeField(verbose_name='End time', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='eventpagecarouselitem',
            name='embed_url',
            field=models.URLField(verbose_name='Embed URL', blank=True),
        ),
        migrations.AlterField(
            model_name='eventpagecarouselitem',
            name='image',
            field=models.ForeignKey(to='wagtailimages.Image', on_delete=django.db.models.deletion.SET_NULL, related_name='+', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='eventpagecarouselitem',
            name='link_document',
            field=models.ForeignKey(to='wagtaildocs.Document', related_name='+', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='eventpagecarouselitem',
            name='link_external',
            field=models.URLField(verbose_name='External link', blank=True),
        ),
        migrations.AlterField(
            model_name='eventpagecarouselitem',
            name='link_page',
            field=models.ForeignKey(to='wagtailcore.Page', related_name='+', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='eventpagecarouselitem',
            name='page',
            field=modelcluster.fields.ParentalKey(to='tests.EventPage', related_name='carousel_items'),
        ),
        migrations.AlterField(
            model_name='eventpagerelatedlink',
            name='link_document',
            field=models.ForeignKey(to='wagtaildocs.Document', related_name='+', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='eventpagerelatedlink',
            name='link_external',
            field=models.URLField(verbose_name='External link', blank=True),
        ),
        migrations.AlterField(
            model_name='eventpagerelatedlink',
            name='link_page',
            field=models.ForeignKey(to='wagtailcore.Page', related_name='+', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='eventpagerelatedlink',
            name='page',
            field=modelcluster.fields.ParentalKey(to='tests.EventPage', related_name='related_links'),
        ),
        migrations.AlterField(
            model_name='eventpagerelatedlink',
            name='title',
            field=models.CharField(max_length=255, help_text='Link title'),
        ),
        migrations.AlterField(
            model_name='eventpagespeaker',
            name='first_name',
            field=models.CharField(max_length=255, verbose_name='Name', blank=True),
        ),
        migrations.AlterField(
            model_name='eventpagespeaker',
            name='image',
            field=models.ForeignKey(to='wagtailimages.Image', on_delete=django.db.models.deletion.SET_NULL, related_name='+', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='eventpagespeaker',
            name='last_name',
            field=models.CharField(max_length=255, verbose_name='Surname', blank=True),
        ),
        migrations.AlterField(
            model_name='eventpagespeaker',
            name='link_document',
            field=models.ForeignKey(to='wagtaildocs.Document', related_name='+', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='eventpagespeaker',
            name='link_external',
            field=models.URLField(verbose_name='External link', blank=True),
        ),
        migrations.AlterField(
            model_name='eventpagespeaker',
            name='link_page',
            field=models.ForeignKey(to='wagtailcore.Page', related_name='+', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='eventpagespeaker',
            name='page',
            field=modelcluster.fields.ParentalKey(to='tests.EventPage', related_name='speakers'),
        ),
        migrations.AlterField(
            model_name='formfield',
            name='field_type',
            field=models.CharField(choices=[('singleline', 'Single line text'), ('multiline', 'Multi-line text'), ('email', 'Email'), ('number', 'Number'), ('url', 'URL'), ('checkbox', 'Checkbox'), ('checkboxes', 'Checkboxes'), ('dropdown', 'Drop down'), ('radio', 'Radio buttons'), ('date', 'Date'), ('datetime', 'Date/time')], max_length=16),
        ),
        migrations.AlterField(
            model_name='formfield',
            name='page',
            field=modelcluster.fields.ParentalKey(to='tests.FormPage', related_name='form_fields'),
        ),
        migrations.AlterField(
            model_name='formpage',
            name='page_ptr',
            field=models.OneToOneField(serialize=False, to='wagtailcore.Page', parent_link=True, auto_created=True, primary_key=True),
        ),
        migrations.AlterField(
            model_name='pagewitholdstyleroutemethod',
            name='page_ptr',
            field=models.OneToOneField(serialize=False, to='wagtailcore.Page', parent_link=True, auto_created=True, primary_key=True),
        ),
        migrations.AlterField(
            model_name='routablepagetest',
            name='page_ptr',
            field=models.OneToOneField(serialize=False, to='wagtailcore.Page', parent_link=True, auto_created=True, primary_key=True),
        ),
        migrations.AlterField(
            model_name='searchtestchild',
            name='searchtest_ptr',
            field=models.OneToOneField(serialize=False, to='tests.SearchTest', parent_link=True, auto_created=True, primary_key=True),
        ),
        migrations.AlterField(
            model_name='simplepage',
            name='page_ptr',
            field=models.OneToOneField(serialize=False, to='wagtailcore.Page', parent_link=True, auto_created=True, primary_key=True),
        ),
        migrations.AlterField(
            model_name='standardchild',
            name='page_ptr',
            field=models.OneToOneField(serialize=False, to='wagtailcore.Page', parent_link=True, auto_created=True, primary_key=True),
        ),
        migrations.AlterField(
            model_name='standardindex',
            name='page_ptr',
            field=models.OneToOneField(serialize=False, to='wagtailcore.Page', parent_link=True, auto_created=True, primary_key=True),
        ),
        migrations.AlterField(
            model_name='taggedpage',
            name='page_ptr',
            field=models.OneToOneField(serialize=False, to='wagtailcore.Page', parent_link=True, auto_created=True, primary_key=True),
        ),
        migrations.AlterField(
            model_name='taggedpagetag',
            name='content_object',
            field=modelcluster.fields.ParentalKey(to='tests.TaggedPage', related_name='tagged_items'),
        ),
        migrations.AlterField(
            model_name='taggedpagetag',
            name='tag',
            field=models.ForeignKey(to='taggit.Tag', related_name='tests_taggedpagetag_items'),
        ),
    ]
