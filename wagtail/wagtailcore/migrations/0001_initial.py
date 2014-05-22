# encoding: utf8
from django.db import models, migrations
from django.conf import settings
import wagtail.wagtailsearch.indexed


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Page',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('path', models.CharField(unique=True, max_length=255)),
                ('depth', models.PositiveIntegerField()),
                ('numchild', models.PositiveIntegerField(default=0)),
                ('title', models.CharField(help_text=u"The page title as you'd like it to be seen by the public", max_length=255)),
                ('slug', models.SlugField(help_text=u'The name of the page as it will appear in URLs e.g http://domain.com/blog/[my-slug]/')),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', to_field=u'id')),
                ('live', models.BooleanField(default=True, editable=False)),
                ('has_unpublished_changes', models.BooleanField(default=False, editable=False)),
                ('url_path', models.CharField(max_length=255, editable=False, blank=True)),
                ('owner', models.ForeignKey(to_field=u'id', blank=True, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
                ('seo_title', models.CharField(help_text=u"Optional. 'Search Engine Friendly' title. This will appear at the top of the browser window.", max_length=255, verbose_name=u'Page title', blank=True)),
                ('show_in_menus', models.BooleanField(default=False, help_text=u'Whether a link to this page will appear in automatically generated menus')),
                ('search_description', models.TextField(blank=True)),
            ],
            options={
                u'abstract': False,
            },
            bases=(models.Model, wagtail.wagtailsearch.indexed.Indexed),
        ),
    ]
