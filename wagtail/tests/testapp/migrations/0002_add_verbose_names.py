# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customimagewithadminformfields',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created at'),
        ),
        migrations.AlterField(
            model_name='customimagewithadminformfields',
            name='height',
            field=models.IntegerField(verbose_name='Height', editable=False),
        ),
        migrations.AlterField(
            model_name='customimagewithadminformfields',
            name='uploaded_by_user',
            field=models.ForeignKey(
                blank=True,
                editable=False,
                to=settings.AUTH_USER_MODEL,
                null=True,
                verbose_name='Uploaded by user'
            ),
        ),
        migrations.AlterField(
            model_name='customimagewithadminformfields',
            name='width',
            field=models.IntegerField(verbose_name='Width', editable=False),
        ),
        migrations.AlterField(
            model_name='customimagewithoutadminformfields',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created at'),
        ),
        migrations.AlterField(
            model_name='customimagewithoutadminformfields',
            name='height',
            field=models.IntegerField(verbose_name='Height', editable=False),
        ),
        migrations.AlterField(
            model_name='customimagewithoutadminformfields',
            name='uploaded_by_user',
            field=models.ForeignKey(
                blank=True,
                editable=False,
                to=settings.AUTH_USER_MODEL,
                null=True,
                verbose_name='Uploaded by user'
            ),
        ),
        migrations.AlterField(
            model_name='customimagewithoutadminformfields',
            name='width',
            field=models.IntegerField(verbose_name='Width', editable=False),
        ),
        migrations.AlterField(
            model_name='formfield',
            name='choices',
            field=models.CharField(
                help_text='Comma separated list of choices. Only applicable in checkboxes, radio and dropdown.',
                max_length=512,
                verbose_name='Choices',
                blank=True
            ),
        ),
        migrations.AlterField(
            model_name='formfield',
            name='default_value',
            field=models.CharField(
                help_text='Default value. Comma separated values supported for checkboxes.',
                max_length=255,
                verbose_name='Default value',
                blank=True
            ),
        ),
        migrations.AlterField(
            model_name='formfield',
            name='field_type',
            field=models.CharField(
                max_length=16,
                verbose_name='Field type',
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
            field=models.CharField(max_length=255, verbose_name='Help text', blank=True),
        ),
        migrations.AlterField(
            model_name='formfield',
            name='label',
            field=models.CharField(help_text='The label of the form field', max_length=255, verbose_name='Label'),
        ),
        migrations.AlterField(
            model_name='formfield',
            name='required',
            field=models.BooleanField(default=True, verbose_name='Required'),
        ),
        migrations.AlterField(
            model_name='formpage',
            name='from_address',
            field=models.CharField(max_length=255, verbose_name='From address', blank=True),
        ),
        migrations.AlterField(
            model_name='formpage',
            name='subject',
            field=models.CharField(max_length=255, verbose_name='Subject', blank=True),
        ),
        migrations.AlterField(
            model_name='formpage',
            name='to_address',
            field=models.CharField(
                help_text='Optional - form submissions will be emailed to this address',
                max_length=255,
                verbose_name='To address',
                blank=True
            ),
        ),
    ]
