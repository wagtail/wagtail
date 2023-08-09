import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0022_add_site_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pagerevision",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                verbose_name="user",
                blank=True,
                to=settings.AUTH_USER_MODEL,
                null=True,
            ),
        ),
    ]
