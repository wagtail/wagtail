from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0096_referenceindex_referenceindex_source_object_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS wagtailcore_revision_content_lookup
                ON wagtailcore_revision (base_content_type_id, object_id, created_at DESC);
            """,
            reverse_sql="""
                DROP INDEX CONCURRENTLY IF EXISTS wagtailcore_revision_content_lookup;
            """,
        ),
    ]
