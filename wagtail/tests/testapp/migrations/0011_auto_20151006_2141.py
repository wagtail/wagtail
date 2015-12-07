# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import taggit.managers
import wagtail.wagtailadmin.taggable
from django.conf import settings
import wagtail.wagtailimages.models


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tests', '0010_mtibasepage_mtichildpage'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(verbose_name='Title', max_length=255)),
                (
                    'file',
                    models.ImageField(
                        verbose_name='File',
                        upload_to=wagtail.wagtailimages.models.get_upload_to,
                        height_field='height',
                        width_field='width'
                    )
                ),
                ('width', models.IntegerField(verbose_name='Width', editable=False)),
                ('height', models.IntegerField(verbose_name='Height', editable=False)),
                ('created_at', models.DateTimeField(db_index=True, verbose_name='Created at', auto_now_add=True)),
                ('focal_point_x', models.PositiveIntegerField(null=True, blank=True)),
                ('focal_point_y', models.PositiveIntegerField(null=True, blank=True)),
                ('focal_point_width', models.PositiveIntegerField(null=True, blank=True)),
                ('focal_point_height', models.PositiveIntegerField(null=True, blank=True)),
                ('file_size', models.PositiveIntegerField(editable=False, null=True)),
                ('caption', models.CharField(max_length=255)),
                ('not_editable_field', models.CharField(max_length=255)),
                (
                    'tags',
                    taggit.managers.TaggableManager(
                        blank=True,
                        help_text=None,
                        through='taggit.TaggedItem',
                        verbose_name='Tags',
                        to='taggit.Tag'
                    )
                ),
                (
                    'uploaded_by_user',
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        verbose_name='Uploaded by user',
                        null=True,
                        to=settings.AUTH_USER_MODEL
                    )
                ),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, wagtail.wagtailadmin.taggable.TagSearchable),
        ),
        migrations.RemoveField(
            model_name='customimagewithadminformfields',
            name='tags',
        ),
        migrations.RemoveField(
            model_name='customimagewithadminformfields',
            name='uploaded_by_user',
        ),
        migrations.RemoveField(
            model_name='customimagewithoutadminformfields',
            name='tags',
        ),
        migrations.RemoveField(
            model_name='customimagewithoutadminformfields',
            name='uploaded_by_user',
        ),
        migrations.DeleteModel(
            name='CustomImageWithAdminFormFields',
        ),
        migrations.DeleteModel(
            name='CustomImageWithoutAdminFormFields',
        ),
    ]
