import sqlite3

from django.db import OperationalError


def fts5_available():
    # based on https://stackoverflow.com/a/36656216/1853523
    if sqlite3.sqlite_version_info < (3, 19, 0):
        # Prior to version 3.19, SQLite doesn't support FTS5 queries with
        # column filters ('{column_1 column_2} : query'), which the sqlite
        # fulltext backend needs
        return False

    tmp_db = sqlite3.connect(":memory:")
    try:
        tmp_db.execute("CREATE VIRTUAL TABLE fts5test USING fts5 (data);")
    except sqlite3.OperationalError:
        return False
    finally:
        tmp_db.close()

    return True


def fts_table_exists():
    from wagtail.search.models import SQLiteFTSIndexEntry

    try:
        # ignore result of query; we are only interested in the query failing,
        # not the presence of index entries
        SQLiteFTSIndexEntry.objects.exists()
    except OperationalError:
        return False

    return True
