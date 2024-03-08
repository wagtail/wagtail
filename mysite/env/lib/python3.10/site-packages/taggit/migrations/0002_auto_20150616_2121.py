from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("taggit", "0001_initial")]

    operations = [
        # this migration was modified from previously being
        # a ModifyIndexTogether operation.
        #
        # If you are a long-enough user of this library, the name
        # of the index does not match what is written here. Please
        # query the DB itself to find out what the name originally was.
        migrations.AddIndex(
            "taggeditem",
            models.Index(
                fields=("content_type", "object_id"),
                # this is not the name of the index in previous version,
                # but this is necessary to deal with index_together issues.
                name="taggit_tagg_content_8fc721_idx",
            ),
        )
    ]
