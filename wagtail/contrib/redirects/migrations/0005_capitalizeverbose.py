from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailredirects", "0004_set_unique_on_path_and_site"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="redirect",
            options={"verbose_name": "redirect"},
        ),
        migrations.AlterField(
            model_name="redirect",
            name="is_permanent",
            field=models.BooleanField(
                default=True,
                help_text="Recommended. Permanent redirects ensure search engines forget the old page (the 'Redirect from') and index the new page instead.",
                verbose_name="permanent",
            ),
        ),
        migrations.AlterField(
            model_name="redirect",
            name="old_path",
            field=models.CharField(
                max_length=255, db_index=True, verbose_name="redirect from"
            ),
        ),
        migrations.AlterField(
            model_name="redirect",
            name="redirect_link",
            field=models.URLField(blank=True, verbose_name="redirect to any URL"),
        ),
        migrations.AlterField(
            model_name="redirect",
            name="redirect_page",
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                blank=True,
                null=True,
                to="wagtailcore.Page",
                verbose_name="redirect to a page",
            ),
        ),
        migrations.AlterField(
            model_name="redirect",
            name="site",
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                blank=True,
                related_name="redirects",
                null=True,
                to="wagtailcore.Site",
                verbose_name="site",
            ),
        ),
    ]
