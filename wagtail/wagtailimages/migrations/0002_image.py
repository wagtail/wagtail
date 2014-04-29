# encoding: utf8
from django.db import models, migrations
import taggit.managers
import taggit.models
import wagtail.wagtailimages.models
from django.conf import settings
import wagtail.wagtailadmin.taggable


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('taggit', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Image',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, verbose_name=u'Title')),
                ('file', models.ImageField(upload_to=wagtail.wagtailimages.models.get_upload_to, width_field='width', height_field='height', validators=[wagtail.wagtailimages.models.file_extension_validator], verbose_name=u'File')),
                ('width', models.IntegerField(editable=False)),
                ('height', models.IntegerField(editable=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('uploaded_by_user', models.ForeignKey(to_field=u'id', blank=True, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
                ('tags', taggit.managers.TaggableManager(to=taggit.models.Tag, through=taggit.models.TaggedItem, blank=True, help_text=None, verbose_name=u'Tags')),
            ],
            options={
                u'abstract': False,
            },
            bases=(models.Model, wagtail.wagtailadmin.taggable.TagSearchable),
        ),
    ]
