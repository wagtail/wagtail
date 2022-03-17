# -*- coding: utf-8 -*-
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0009_remove_auto_now_add_from_pagerevision_created_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="page",
            name="owner",
            field=models.ForeignKey(
                related_name="owned_pages",
                on_delete=django.db.models.deletion.SET_NULL,
                blank=True,
                editable=False,
                to=settings.AUTH_USER_MODEL,
                null=True,
            ),
        ),
    ]
