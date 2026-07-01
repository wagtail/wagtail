from django.db import connection, migrations, models

# Copied from 0003_add_text_fields in modelsearch

class Migration(migrations.Migration):
    dependencies = [
        ("wagtailsearch", "0009_remove_ngram_autocomplete"),
    ]

    if connection.vendor == "postgresql":
        operations = [
            migrations.AddField(
                model_name="indexentry",
                name="title_text",
                field=models.TextField(default=""),
            ),
            migrations.AddField(
                model_name="indexentry",
                name="body_text",
                field=models.TextField(default=""),
            ),
            # GIN trigram indexes are created by the enable_trigram
            # management command, not here. The reverse SQL drops them on
            # migration rollback.
            migrations.RunSQL(
                sql=migrations.RunSQL.noop,
                reverse_sql="DROP INDEX IF EXISTS modelsearch_title_text_trgm;",
            ),
            migrations.RunSQL(
                sql=migrations.RunSQL.noop,
                reverse_sql="DROP INDEX IF EXISTS modelsearch_body_text_trgm;",
            ),
            migrations.RunSQL(
                sql=migrations.RunSQL.noop,
                reverse_sql="DROP INDEX IF EXISTS modelsearch_title_text_unaccent_trgm;",
            ),
            migrations.RunSQL(
                sql=migrations.RunSQL.noop,
                reverse_sql="DROP INDEX IF EXISTS modelsearch_body_text_unaccent_trgm;",
            ),
        ]
    else:
        operations = []
