from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailusers", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="approved_notifications",
            field=models.BooleanField(
                default=True,
                help_text="Receive notification when your page edit is approved",
                verbose_name="Approved notifications",
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="rejected_notifications",
            field=models.BooleanField(
                default=True,
                help_text="Receive notification when your page edit is rejected",
                verbose_name="Rejected notifications",
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="submitted_notifications",
            field=models.BooleanField(
                default=True,
                help_text="Receive notification when a page is submitted for moderation",
                verbose_name="Submitted notifications",
            ),
            preserve_default=True,
        ),
    ]
