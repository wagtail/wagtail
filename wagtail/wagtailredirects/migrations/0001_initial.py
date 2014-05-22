# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0005_initial_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='Redirect',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('old_path', models.CharField(unique=True, max_length=255, verbose_name=u'Redirect from', db_index=True)),
                ('site', models.ForeignKey(to_field=u'id', blank=True, editable=False, to='wagtailcore.Site', null=True)),
                ('is_permanent', models.BooleanField(default=True, help_text=u"Recommended. Permanent redirects ensure search engines forget the old page (the 'Redirect from') and index the new page instead.", verbose_name=u'Permanent')),
                ('redirect_page', models.ForeignKey(verbose_name=u'Redirect to a page', to_field=u'id', blank=True, to='wagtailcore.Page', null=True)),
                ('redirect_link', models.URLField(verbose_name=u'Redirect to any URL', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
