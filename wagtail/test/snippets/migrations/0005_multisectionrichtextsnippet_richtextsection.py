# -*- coding: utf-8 -*-
from django.db import migrations, models
import wagtail.core.fields
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('snippetstests', '0004_fileuploadsnippet'),
    ]

    operations = [
        migrations.CreateModel(
            name='MultiSectionRichTextSnippet',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RichTextSection',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('body', wagtail.core.fields.RichTextField()),
                ('snippet', modelcluster.fields.ParentalKey(to='snippetstests.MultiSectionRichTextSnippet', related_name='sections', on_delete=models.CASCADE)),
            ],
        ),
    ]
