from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("demosite", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="homepage",
            options={"verbose_name": "homepage"},
        ),
    ]
