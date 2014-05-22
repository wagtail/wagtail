# encoding: utf8
from django.db import models, migrations
import wagtail.wagtailsearch.indexed


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0005_initial_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='Query',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('query_string', models.CharField(unique=True, max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SearchTest',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('content', models.TextField()),
                ('live', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model, wagtail.wagtailsearch.indexed.Indexed),
        ),
        migrations.CreateModel(
            name='EditorsPick',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('query', models.ForeignKey(to='wagtailsearch.Query', to_field=u'id')),
                ('page', models.ForeignKey(to='wagtailcore.Page', to_field=u'id')),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                u'ordering': ('sort_order',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='QueryDailyHits',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('query', models.ForeignKey(to='wagtailsearch.Query', to_field=u'id')),
                ('date', models.DateField()),
                ('hits', models.IntegerField(default=0)),
            ],
            options={
                u'unique_together': set([('query', 'date')]),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SearchTestChild',
            fields=[
                (u'searchtest_ptr', models.OneToOneField(auto_created=True, primary_key=True, to_field=u'id', serialize=False, to='wagtailsearch.SearchTest')),
                ('extra_content', models.TextField()),
            ],
            options={
            },
            bases=('wagtailsearch.searchtest',),
        ),
    ]
