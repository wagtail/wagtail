from django.db import models
from django.db.models import OneToOneField
from modelsearch.abstract_models import AbstractIndexEntry, AbstractSQLiteFTSIndexEntry


class IndexEntry(AbstractIndexEntry):
    """
    The IndexEntry model that will get created in the database.
    """

    class Meta(AbstractIndexEntry.Meta):
        """
        Contains everything in the AbstractIndexEntry Meta class, but makes this model concrete.
        """

        abstract = False


if AbstractSQLiteFTSIndexEntry:

    class SQLiteFTSIndexEntry(AbstractSQLiteFTSIndexEntry):
        """
        The SQLite FTS IndexEntry model that will get created in the database if using SQLite with FTS5 support.
        """

        index_entry = OneToOneField(
            primary_key=True,
            to=IndexEntry,
            on_delete=models.CASCADE,
            db_column="rowid",
        )

        class Meta(AbstractSQLiteFTSIndexEntry.Meta):
            """
            Contains everything in the AbstractSQLiteFTSIndexEntry Meta class, but makes this model concrete.
            """

            abstract = False
            db_table = "wagtailsearch_indexentry_fts"
