# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-31 00:31
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('wagtailcore', '0028_merge'), ('tests', '0003_onetoonepage')]

    operations = [
        migrations.CreateModel(
            name='FileUploadSetting',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('file', models.FileField(upload_to='')),
                (
                    'site',
                    models.OneToOneField(
                        editable=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        to='wagtailcore.Site',
                    ),
                ),
            ],
            options={'abstract': False},
        )
    ]
