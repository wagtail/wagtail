# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0005_initial_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='Embed',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField()),
                ('max_width', models.SmallIntegerField(null=True, blank=True)),
                ('type', models.CharField(max_length=10, choices=[('video', 'Video'), ('photo', 'Photo'), ('link', 'Link'), ('rich', 'Rich')])),
                ('html', models.TextField(blank=True)),
                ('title', models.TextField(blank=True)),
                ('thumbnail_url', models.URLField(null=True, blank=True)),
                ('width', models.IntegerField(null=True, blank=True)),
                ('height', models.IntegerField(null=True, blank=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                u'unique_together': set([('url', 'max_width')]),
            },
            bases=(models.Model,),
        ),
    ]
