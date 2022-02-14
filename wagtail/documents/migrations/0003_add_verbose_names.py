# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wagtaildocs", "0002_initial_data"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="document",
            options={"verbose_name": "Document"},
        ),
        migrations.AlterField(
            model_name="document",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Created at"),
        ),
        migrations.AlterField(
            model_name="document",
            name="uploaded_by_user",
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                blank=True,
                editable=False,
                to=settings.AUTH_USER_MODEL,
                null=True,
                verbose_name="Uploaded by user",
            ),
        ),
    ]
