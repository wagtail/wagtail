# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('wagtailcore', '0021_collection_initial_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupCollectionPermission',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('collection', models.ForeignKey(related_name='group_permissions', verbose_name='collection', to='wagtailcore.Collection')),
                ('group', models.ForeignKey(related_name='collection_permissions', verbose_name='group', to='auth.Group')),
                ('permission', models.ForeignKey(to='auth.Permission', verbose_name='permission')),
            ],
            options={
                'verbose_name': 'group collection permission',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='groupcollectionpermission',
            unique_together=set([('group', 'collection', 'permission')]),
        ),
    ]
