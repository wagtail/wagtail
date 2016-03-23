# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),

                (
                    'last_login',
                    models.DateTimeField(null=True, verbose_name='last login', blank=True)
                ),

                ('is_superuser',
                    models.BooleanField(
                        default=False,
                        help_text='Designates that this user has all permissions without explicitly assigning them.',
                        verbose_name='superuser status'
                    )),
                ('username', models.CharField(unique=True, max_length=100)),
                ('email', models.EmailField(max_length=255, blank=True)),
                ('is_staff', models.BooleanField(default=True)),
                ('is_active', models.BooleanField(default=True)),
                ('first_name', models.CharField(max_length=50, blank=True)),
                ('last_name', models.CharField(max_length=50, blank=True)),
                (
                    'groups',
                    models.ManyToManyField(
                        related_query_name='user',
                        related_name='user_set',
                        to='auth.Group',
                        blank=True,
                        help_text=(
                            "The groups this user belongs to. "
                            "A user will get all permissions granted to each of their groups."
                        ),
                        verbose_name='groups'
                    )
                ),
                (
                    'user_permissions',
                    models.ManyToManyField(
                        to='auth.Permission',
                        verbose_name='user permissions',
                        help_text='Specific permissions for this user.',
                        related_name='user_set',
                        blank=True,
                        related_query_name='user'
                    )
                )
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EmailUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                (
                    'last_login',
                    models.DateTimeField(null=True, verbose_name='last login', blank=True)
                ),
                ('email', models.EmailField(unique=True, max_length=255)),
                ('is_staff', models.BooleanField(default=True)),
                ('is_active', models.BooleanField(default=True)),
                ('first_name', models.CharField(max_length=50, blank=True)),
                ('last_name', models.CharField(max_length=50, blank=True)),
                ('is_superuser', models.BooleanField(default=False)),
                ('groups', models.ManyToManyField(related_name='+', to='auth.Group', blank=True)),
                ('user_permissions', models.ManyToManyField(related_name='+', to='auth.Permission', blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
