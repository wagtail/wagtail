# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('wagtailcore', '0025_collection_initial_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupCollectionPermission',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('collection', models.ForeignKey(related_name='group_permissions', verbose_name='collection', to='wagtailcore.Collection', on_delete=models.CASCADE)),
                ('group', models.ForeignKey(related_name='collection_permissions', verbose_name='group', to='auth.Group', on_delete=models.CASCADE)),
                ('permission', models.ForeignKey(to='auth.Permission', verbose_name='permission', on_delete=models.CASCADE)),
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
