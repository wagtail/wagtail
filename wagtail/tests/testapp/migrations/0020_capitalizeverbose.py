# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import wagtail.wagtailimages.models
import taggit.managers
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0019_customimagefilepath'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customimage',
            name='created_at',
            field=models.DateTimeField(db_index=True, auto_now_add=True, verbose_name='created at'),
        ),
        migrations.AlterField(
            model_name='customimage',
            name='file',
            field=models.ImageField(
                width_field='width',
                height_field='height',
                verbose_name='file',
                upload_to=wagtail.wagtailimages.models.get_upload_to
            ),
        ),
        migrations.AlterField(
            model_name='customimage',
            name='height',
            field=models.IntegerField(editable=False, verbose_name='height'),
        ),
        migrations.AlterField(
            model_name='customimage',
            name='tags',
            field=taggit.managers.TaggableManager(
                help_text=None,
                blank=True,
                through='taggit.TaggedItem',
                to='taggit.Tag',
                verbose_name='tags'
            ),
        ),
        migrations.AlterField(
            model_name='customimage',
            name='title',
            field=models.CharField(max_length=255, verbose_name='title'),
        ),
        migrations.AlterField(
            model_name='customimage',
            name='uploaded_by_user',
            field=models.ForeignKey(
                editable=False,
                blank=True,
                to=settings.AUTH_USER_MODEL,
                null=True, verbose_name='uploaded by user'
            ),
        ),
        migrations.AlterField(
            model_name='customimage',
            name='width',
            field=models.IntegerField(editable=False, verbose_name='width'),
        ),
        migrations.AlterField(
            model_name='customimagefilepath',
            name='created_at',
            field=models.DateTimeField(db_index=True, auto_now_add=True, verbose_name='created at'),
        ),
        migrations.AlterField(
            model_name='customimagefilepath',
            name='file',
            field=models.ImageField(
                width_field='width',
                height_field='height',
                verbose_name='file',
                upload_to=wagtail.wagtailimages.models.get_upload_to
            ),
        ),
        migrations.AlterField(
            model_name='customimagefilepath',
            name='height',
            field=models.IntegerField(editable=False, verbose_name='height'),
        ),
        migrations.AlterField(
            model_name='customimagefilepath',
            name='tags',
            field=taggit.managers.TaggableManager(
                help_text=None,
                blank=True,
                through='taggit.TaggedItem',
                to='taggit.Tag',
                verbose_name='tags'
            ),
        ),
        migrations.AlterField(
            model_name='customimagefilepath',
            name='title',
            field=models.CharField(max_length=255, verbose_name='title'),
        ),
        migrations.AlterField(
            model_name='customimagefilepath',
            name='uploaded_by_user',
            field=models.ForeignKey(
                editable=False,
                blank=True,
                to=settings.AUTH_USER_MODEL,
                null=True,
                verbose_name='uploaded by user'
            ),
        ),
        migrations.AlterField(
            model_name='customimagefilepath',
            name='width',
            field=models.IntegerField(editable=False, verbose_name='width'),
        ),
        migrations.AlterField(
            model_name='formfield',
            name='choices',
            field=models.CharField(
                help_text='Comma separated list of choices. Only applicable in checkboxes, radio and dropdown.',
                max_length=512,
                blank=True,
                verbose_name='choices'
            ),
        ),
        migrations.AlterField(
            model_name='formfield',
            name='default_value',
            field=models.CharField(
                help_text='Default value. Comma separated values supported for checkboxes.',
                max_length=255,
                blank=True,
                verbose_name='default value'
            ),
        ),
        migrations.AlterField(
            model_name='formfield',
            name='field_type',
            field=models.CharField(
                max_length=16,
                verbose_name='field type',
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
                ]
            ),
        ),
        migrations.AlterField(
            model_name='formfield',
            name='help_text',
            field=models.CharField(max_length=255, blank=True, verbose_name='help text'),
        ),
        migrations.AlterField(
            model_name='formfield',
            name='label',
            field=models.CharField(help_text='The label of the form field', max_length=255, verbose_name='label'),
        ),
        migrations.AlterField(
            model_name='formfield',
            name='required',
            field=models.BooleanField(default=True, verbose_name='required'),
        ),
        migrations.AlterField(
            model_name='formpage',
            name='from_address',
            field=models.CharField(max_length=255, blank=True, verbose_name='from address'),
        ),
        migrations.AlterField(
            model_name='formpage',
            name='subject',
            field=models.CharField(max_length=255, blank=True, verbose_name='subject'),
        ),
        migrations.AlterField(
            model_name='formpage',
            name='to_address',
            field=models.CharField(
                help_text='Optional - form submissions will be emailed to this address',
                max_length=255,
                blank=True,
                verbose_name='to address'
            ),
        ),
    ]
