# Generated by Django 3.2.4 on 2021-06-28 14:12

import django.contrib.postgres.indexes
import django.contrib.postgres.search
from django.db import connection, migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('wagtailsearch', '0004_querydailyhits_verbose_name_plural'),
    ]

    if connection.vendor == 'postgresql':
        operations = [
            migrations.CreateModel(
                name='IndexEntry',
                fields=[
                    ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                    ('object_id', models.TextField()),
                    ('title_norm', models.FloatField(default=1.0)),
                    ('autocomplete', django.contrib.postgres.search.SearchVectorField()),
                    ('title', django.contrib.postgres.search.SearchVectorField()),
                    ('body', django.contrib.postgres.search.SearchVectorField()),
                    ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='contenttypes.contenttype')),
                ],
                options={
                    'verbose_name': 'index entry',
                    'verbose_name_plural': 'index entries',
                    'abstract': False,
                },
            ),
            migrations.AddIndex(
                model_name='indexentry',
                index=django.contrib.postgres.indexes.GinIndex(fields=['autocomplete'], name='wagtailsear_autocom_476c89_gin'),
            ),
            migrations.AddIndex(
                model_name='indexentry',
                index=django.contrib.postgres.indexes.GinIndex(fields=['title'], name='wagtailsear_title_9caae0_gin'),
            ),
            migrations.AddIndex(
                model_name='indexentry',
                index=django.contrib.postgres.indexes.GinIndex(fields=['body'], name='wagtailsear_body_90c85d_gin'),
            ),
            migrations.AlterUniqueTogether(
                name='indexentry',
                unique_together={('content_type', 'object_id')},
            ),
        ]
    else:
        operations = []
