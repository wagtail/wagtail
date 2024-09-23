from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailimages", "0016_deprecate_rendition_filter_relation"),
    ]

    operations = [
        # The Wagtail 1.8 version of migration wagtailimages/0016 did not include the
        # step to reduce focal_point_key's max_length to 16, necessary to make it work
        # on some MySQL configurations. This migration (added in 1.8.1) ensures that
        # installations that were already successfully running 1.8 receive this change
        # on upgrading to 1.8.1 or later.
        migrations.AlterField(
            model_name="rendition",
            name="focal_point_key",
            field=models.CharField(
                blank=True, default="", max_length=16, editable=False
            ),
        ),
    ]
