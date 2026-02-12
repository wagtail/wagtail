from django.db import connection, migrations

# This migration takes on the base model defined in 0005_create_indexentry and adds certain fields that are specific to each database system
class Migration(migrations.Migration):

    dependencies = [
        ("wagtailsearch", "0008_remove_query_and_querydailyhits_models"),
    ]

    # Reverse the usage of ngram parser with MySQL introduced in
    # ``0006_customise_indexentry.py``.
    #
    # Ngram parser is designed primarily for languages which to not use spaces to
    # delimit words (most commonly CJK languages). When using ngram with English or
    # other non-CJK languages, it has the adverse affect of parsing words into
    # non-sensical queries that return no results. MySQL default ngram token size is 2
    # characters, so for example the word "wagtail" would be parsed into 6 separate
    # words as follows":
    #
    #    "wa" "ag" "gt" "ta" "ai" "il"
    #
    # In English, these tokens would provide useless search results, and in most cases,
    # no results are returned at all when using autocomplete from the Wagtail admin.
    #
    # See: https://dev.mysql.com/doc/refman/8.0/en/fulltext-search-ngram.html
    if connection.vendor == "mysql" and not connection.mysql_is_mariadb:
        operations = [
            migrations.RunSQL(
                sql="""
                ALTER TABLE wagtailsearch_indexentry
                    DROP INDEX `fulltext_autocomplete`;

                ALTER TABLE wagtailsearch_indexentry
                    ADD FULLTEXT INDEX `fulltext_autocomplete` (`autocomplete`);
                """,
                reverse_sql="""
                ALTER TABLE wagtailsearch_indexentry
                    DROP INDEX `fulltext_autocomplete`;

                ALTER TABLE wagtailsearch_indexentry
                    ADD FULLTEXT INDEX `fulltext_autocomplete` (`autocomplete`)
                    WITH PARSER ngram;
                """,
            )
        ]
