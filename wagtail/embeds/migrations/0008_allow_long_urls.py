from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailembeds", "0007_populate_hash"),
    ]

    operations = [
        migrations.AlterField(
            model_name="embed",
            name="hash",
            field=models.CharField(db_index=True, max_length=32, unique=True),
        ),
        # MySQL needs max length on the unique together fields.
        # Drop unique together before alter char to text.
        migrations.AlterUniqueTogether(
            name="embed",
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name="embed",
            name="url",
            field=models.TextField(),
        ),
        # Converting URLField to TextField with a default specified (even with preserve_default=False)
        # fails with Django 3.0 and MySQL >=8.0.13 (see https://code.djangoproject.com/ticket/32503) -
        # work around this by altering in two stages, first making the URLField non-null then converting
        # to TextField
        migrations.AlterField(
            model_name="embed",
            name="thumbnail_url",
            field=models.URLField(
                blank=True,
                default="",
                max_length=255,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="embed",
            name="thumbnail_url",
            field=models.TextField(
                blank=True,
            ),
        ),
    ]
