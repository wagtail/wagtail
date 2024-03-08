# This migration has no effect in practice. It exists to stop
# Django from autodetecting migrations in taggit when users
# update to Django 4.0.
# See https://docs.djangoproject.com/en/stable/releases/4.0/#migrations-autodetector-changes
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("taggit", "0003_taggeditem_add_unique_index"),
    ]

    operations = [
        migrations.AlterField(
            model_name="taggeditem",
            name="content_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(app_label)s_%(class)s_tagged_items",
                to="contenttypes.contenttype",
                verbose_name="content type",
            ),
        ),
        migrations.AlterField(
            model_name="taggeditem",
            name="tag",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(app_label)s_%(class)s_items",
                to="taggit.tag",
            ),
        ),
    ]
