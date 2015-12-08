# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import taggit.managers
import wagtail.wagtailimages.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0018_singletonpage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customimage',
            name='created_at',
            field=models.DateTimeField(verbose_name='created at', db_index=True, auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='customimage',
            name='file',
            field=models.ImageField(width_field='width', verbose_name='file', height_field='height', upload_to=wagtail.wagtailimages.models.get_upload_to),
        ),
        migrations.AlterField(
            model_name='customimage',
            name='height',
            field=models.IntegerField(editable=False, verbose_name='height'),
        ),
        migrations.AlterField(
            model_name='customimage',
            name='tags',
            field=taggit.managers.TaggableManager(help_text=None, blank=True, through='taggit.TaggedItem', to='taggit.Tag', verbose_name='tags'),
        ),
        migrations.AlterField(
            model_name='customimage',
            name='title',
            field=models.CharField(verbose_name='title', max_length=255),
        ),
        migrations.AlterField(
            model_name='customimage',
            name='uploaded_by_user',
            field=models.ForeignKey(blank=True, verbose_name='uploaded by user', to=settings.AUTH_USER_MODEL, editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='customimage',
            name='width',
            field=models.IntegerField(editable=False, verbose_name='width'),
        ),
        migrations.AlterField(
            model_name='formfield',
            name='choices',
            field=models.CharField(help_text='Comma separated list of choices. Only applicable in checkboxes, radio and dropdown.', blank=True, verbose_name='choices', max_length=512),
        ),
        migrations.AlterField(
            model_name='formfield',
            name='default_value',
            field=models.CharField(help_text='Default value. Comma separated values supported for checkboxes.', blank=True, verbose_name='default value', max_length=255),
        ),
        migrations.AlterField(
            model_name='formfield',
            name='field_type',
            field=models.CharField(max_length=16, verbose_name='field type', choices=[('singleline', 'Single line text'), ('multiline', 'Multi-line text'), ('email', 'Email'), ('number', 'Number'), ('url', 'URL'), ('checkbox', 'Checkbox'), ('checkboxes', 'Checkboxes'), ('dropdown', 'Drop down'), ('radio', 'Radio buttons'), ('date', 'Date'), ('datetime', 'Date/time')]),
        ),
        migrations.AlterField(
            model_name='formfield',
            name='help_text',
            field=models.CharField(blank=True, verbose_name='help text', max_length=255),
        ),
        migrations.AlterField(
            model_name='formfield',
            name='label',
            field=models.CharField(help_text='The label of the form field', verbose_name='label', max_length=255),
        ),
        migrations.AlterField(
            model_name='formfield',
            name='required',
            field=models.BooleanField(default=True, verbose_name='required'),
        ),
        migrations.AlterField(
            model_name='formpage',
            name='from_address',
            field=models.CharField(blank=True, verbose_name='from address', max_length=255),
        ),
        migrations.AlterField(
            model_name='formpage',
            name='subject',
            field=models.CharField(blank=True, verbose_name='subject', max_length=255),
        ),
        migrations.AlterField(
            model_name='formpage',
            name='to_address',
            field=models.CharField(help_text='Optional - form submissions will be emailed to this address', blank=True, verbose_name='to address', max_length=255),
        ),
    ]
