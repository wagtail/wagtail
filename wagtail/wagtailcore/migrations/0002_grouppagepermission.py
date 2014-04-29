# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0001_initial'),
        ('auth', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupPagePermission',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('group', models.ForeignKey(to='auth.Group', to_field=u'id')),
                ('page', models.ForeignKey(to='wagtailcore.Page', to_field=u'id')),
                ('permission_type', models.CharField(max_length=20, choices=[('add', 'Add'), ('edit', 'Edit'), ('publish', 'Publish')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
