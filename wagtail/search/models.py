from django.db import models
from django.db.models import OneToOneField
from modelsearch.abstract_models import AbstractIndexEntry, AbstractSQLiteFTSIndexEntry

# We import abstract models from the modelsearch app and define concrete implementations here in the
# wagtail.search app. This preserves backwards compatibility for existing Wagtail projects that have
# these models in the wagtailsearch namespace, and avoids the need to add modelsearch to INSTALLED_APPS.


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
    # The SQLite backend additionally requires a second model with a OneToOneField to IndexEntry. If a
    # SQLite connection is in use, modelsearch will define a AbstractSQLiteFTSIndexEntry model
    # (otherwise this will be None).

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
