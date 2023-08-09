from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailusers", "0002_add_verbose_name_on_userprofile"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="userprofile",
            options={"verbose_name": "User Profile"},
        ),
    ]
