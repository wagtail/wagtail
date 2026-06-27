from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailadmin", "0006_formstate"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="formstate",
            name="formstate_user_object",
        ),
        migrations.AddConstraint(
            model_name="formstate",
            constraint=models.UniqueConstraint(
                fields=["user", "content_type", "object_id", "parent_object_id"],
                name="formstate_user_object_unique",
            ),
        ),
    ]