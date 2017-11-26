# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailusers', '0003_add_verbose_names'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='userprofile',
            options={'verbose_name': 'user profile'},
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='approved_notifications',
            field=models.BooleanField(default=True, help_text='Receive notification when your page edit is approved', verbose_name='approved notifications'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='rejected_notifications',
            field=models.BooleanField(default=True, help_text='Receive notification when your page edit is rejected', verbose_name='rejected notifications'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='submitted_notifications',
            field=models.BooleanField(default=True, help_text='Receive notification when a page is submitted for moderation', verbose_name='submitted notifications'),
        ),
    ]
