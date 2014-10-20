# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0008_populate_latest_revision_created_at'),
        ('tests', '0004_auto_20141008_0420'),
    ]

    operations = [
        migrations.CreateModel(
            name='HideableFormField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('label', models.CharField(help_text='The label of the form field', max_length=255)),
                ('field_type', models.CharField(max_length=16, choices=[('singleline', 'Single line text'), ('multiline', 'Multi-line text'), ('email', 'Email'), ('number', 'Number'), ('url', 'URL'), ('checkbox', 'Checkbox'), ('checkboxes', 'Checkboxes'), ('dropdown', 'Drop down'), ('radio', 'Radio buttons'), ('date', 'Date'), ('datetime', 'Date/time')])),
                ('required', models.BooleanField(default=True)),
                ('choices', models.CharField(help_text='Comma separated list of choices. Only applicable in checkboxes, radio and dropdown.', max_length=512, blank=True)),
                ('default_value', models.CharField(help_text='Default value. Comma separated values supported for checkboxes.', max_length=255, blank=True)),
                ('help_text', models.CharField(max_length=255, blank=True)),
                ('is_hidden', models.BooleanField(default=False, help_text='If set, this field will not be shown to the user, but its default value will be submitted with the form.')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HideableFormPage',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.AddField(
            model_name='hideableformfield',
            name='page',
            field=modelcluster.fields.ParentalKey(related_name='form_fields', to='tests.HideableFormPage'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='formfield',
            name='choices',
            field=models.CharField(help_text='Comma separated list of choices. Only applicable in checkboxes, radio and dropdown.', max_length=512, blank=True),
        ),
        migrations.AlterField(
            model_name='formfield',
            name='default_value',
            field=models.CharField(help_text='Default value. Comma separated values supported for checkboxes.', max_length=255, blank=True),
        ),
    ]
