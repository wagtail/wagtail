# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0016_change_page_url_path_to_text_field"),
    ]

    operations = [
        migrations.AlterField(
            model_name="grouppagepermission",
            name="permission_type",
            field=models.CharField(
                choices=[
                    ("add", "Add/edit pages you own"),
                    ("edit", "Edit any page"),
                    ("publish", "Publish any page"),
                    ("lock", "Lock/unlock any page"),
                ],
                max_length=20,
                verbose_name="Permission type",
            ),
            preserve_default=True,
        ),
    ]
