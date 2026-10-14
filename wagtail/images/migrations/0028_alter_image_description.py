from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailimages", "0027_image_description"),
    ]

    operations = [
        migrations.AlterField(
            model_name="image",
            name="description",
            field=models.TextField(
                blank=True,
                default="",
                help_text="A description of the image used as alt text. If left blank, the title will be used as alt text. For accessibility, it is recommended to keep alt text to 150 characters or fewer.",
                verbose_name="description",
            ),
        ),
    ]
