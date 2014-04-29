# encoding: utf8
from django.db import models, migrations
from django.conf import settings
import taggit.models
import wagtail.wagtailadmin.taggable
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('taggit', '__first__'),
        ('wagtailcore', '0005_initial_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, verbose_name=u'Title')),
                ('file', models.FileField(upload_to='documents', verbose_name=u'File')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('uploaded_by_user', models.ForeignKey(to_field=u'id', blank=True, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
                ('tags', taggit.managers.TaggableManager(to=taggit.models.Tag, through=taggit.models.TaggedItem, blank=True, help_text=None, verbose_name=u'Tags')),
            ],
            options={
            },
            bases=(models.Model, wagtail.wagtailadmin.taggable.TagSearchable),
        ),
    ]
