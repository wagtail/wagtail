# -*- coding: utf-8 -*-
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0009_capitalizeverbose'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='uploaded_by_user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL, blank=True, editable=False,
                to=settings.AUTH_USER_MODEL, null=True, verbose_name='uploaded by user'
            ),
        ),
    ]
