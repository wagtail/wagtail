from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("taggit", "0002_auto_20150616_2121"),
    ]

    operations = [
        # this migration was modified to declare a uniqueness constraint differently
        # this change was written on 2023-09-20, if any issues occurred from this please report it upstream
        migrations.AddConstraint(
            model_name="taggeditem",
            constraint=models.UniqueConstraint(
                fields=("content_type", "object_id", "tag"),
                name="taggit_taggeditem_content_type_id_object_id_tag_id_4bb97a8e_uniq",
            ),
        ),
    ]
