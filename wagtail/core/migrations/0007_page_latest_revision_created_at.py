# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0006_add_lock_page_permission'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='latest_revision_created_at',
            field=models.DateTimeField(editable=False, null=True),
            preserve_default=True,
        ),
    ]
