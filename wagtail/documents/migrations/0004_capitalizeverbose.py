import taggit.managers
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wagtaildocs", "0003_add_verbose_names"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="document",
            options={"verbose_name": "document"},
        ),
        migrations.AlterField(
            model_name="document",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="created at"),
        ),
        migrations.AlterField(
            model_name="document",
            name="file",
            field=models.FileField(upload_to="documents", verbose_name="file"),
        ),
        migrations.AlterField(
            model_name="document",
            name="tags",
            field=taggit.managers.TaggableManager(
                through="taggit.TaggedItem",
                verbose_name="tags",
                blank=True,
                help_text=None,
                to="taggit.Tag",
            ),
        ),
        migrations.AlterField(
            model_name="document",
            name="title",
            field=models.CharField(max_length=255, verbose_name="title"),
        ),
        migrations.AlterField(
            model_name="document",
            name="uploaded_by_user",
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                blank=True,
                null=True,
                to=settings.AUTH_USER_MODEL,
                editable=False,
                verbose_name="uploaded by user",
            ),
        ),
    ]
