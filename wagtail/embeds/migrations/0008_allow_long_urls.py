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
        migrations.AlterField(
            model_name="embed",
            name="thumbnail_url",
            field=models.TextField(
                blank=True,
                default="",
            ),
            preserve_default=False,
        ),
    ]
