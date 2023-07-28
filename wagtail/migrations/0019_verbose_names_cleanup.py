from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0018_pagerevision_submitted_for_moderation_index"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="grouppagepermission",
            options={
                "verbose_name": "group page permission",
                "verbose_name_plural": "group page permissions",
            },
        ),
        migrations.AlterModelOptions(
            name="page",
            options={"verbose_name": "page", "verbose_name_plural": "pages"},
        ),
        migrations.AlterModelOptions(
            name="pagerevision",
            options={
                "verbose_name": "page revision",
                "verbose_name_plural": "page revisions",
            },
        ),
        migrations.AlterModelOptions(
            name="pageviewrestriction",
            options={
                "verbose_name": "page view restriction",
                "verbose_name_plural": "page view restrictions",
            },
        ),
        migrations.AlterModelOptions(
            name="site",
            options={"verbose_name": "site", "verbose_name_plural": "sites"},
        ),
    ]
