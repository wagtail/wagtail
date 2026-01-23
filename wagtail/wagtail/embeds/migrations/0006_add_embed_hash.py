from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailembeds", "0005_specify_thumbnail_url_max_length"),
    ]

    operations = [
        migrations.AddField(
            model_name="embed",
            name="hash",
            field=models.CharField(blank=True, max_length=32),
        ),
    ]
