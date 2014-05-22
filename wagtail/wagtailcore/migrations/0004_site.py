# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0003_pagerevision'),
    ]

    operations = [
        migrations.CreateModel(
            name='Site',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('hostname', models.CharField(unique=True, max_length=255, db_index=True)),
                ('port', models.IntegerField(default=80, help_text=u'Set this to something other than 80 if you need a specific port number to appear in URLs (e.g. development on port 8000). Does not affect request handling (so port forwarding still works).')),
                ('root_page', models.ForeignKey(to='wagtailcore.Page', to_field=u'id')),
                ('is_default_site', models.BooleanField(default=False, help_text=u'If true, this site will handle requests for all other hostnames that do not have a site entry of their own')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
