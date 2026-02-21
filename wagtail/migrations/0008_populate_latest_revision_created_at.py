from django.db import migrations
from django.db.models import OuterRef, Subquery

def populate_latest_revision_created_at(apps, schema_editor):
    Page = apps.get_model("wagtailcore.Page")
    PageRevision = apps.get_model("wagtailcore.PageRevision")

    Page.objects.update(
        latest_revision_created_at=Subquery(
            PageRevision.objects.filter(page=OuterRef("pk"))
            .order_by("-created_at")
            .values("created_at")[:1]
        )
    )


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0007_page_latest_revision_created_at"),
    ]

    operations = [
        migrations.RunPython(populate_latest_revision_created_at),
    ]
