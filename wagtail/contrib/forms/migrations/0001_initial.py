# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0002_initial_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='FormSubmission',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('form_data', models.TextField()),
                ('submit_time', models.DateTimeField(auto_now_add=True)),
                ('page', models.ForeignKey(on_delete=models.CASCADE, to='wagtailcore.Page')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
