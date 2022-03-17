# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0005_add_page_lock_permission_to_moderators"),
    ]

    operations = [
        migrations.AlterField(
            model_name="grouppagepermission",
            name="permission_type",
            field=models.CharField(
                max_length=20,
                choices=[
                    ("add", "Add/edit pages you own"),
                    ("edit", "Add/edit any page"),
                    ("publish", "Publish any page"),
                    ("lock", "Lock/unlock any page"),
                ],
            ),
        ),
    ]
