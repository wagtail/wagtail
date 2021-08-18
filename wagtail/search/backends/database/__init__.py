from django.db import connection


def SearchBackend(params):
    """
    Returns the appropriate search backend for the current 'default' database system
    """
    if connection.vendor == 'postgresql':
        from .postgres.postgres import PostgresSearchBackend
        return PostgresSearchBackend(params)
    elif connection.vendor == 'mysql':
        from .mysql.mysql import MySQLSearchBackend
        return MySQLSearchBackend(params)
    elif connection.vendor == 'sqlite':
        import sqlite3
        if sqlite3.sqlite_version_info < (3, 19, 0):
            # Prior to version 3.19, SQLite doesn't support FTS5 queries with column filters ('{column_1 column_2} : query'), so we need to fall back to the dummy fallback backend.
            from .fallback import DatabaseSearchBackend
            return DatabaseSearchBackend(params)
        else:
            from .sqlite.sqlite import SQLiteSearchBackend
            return SQLiteSearchBackend(params)
    else:
        from .fallback import DatabaseSearchBackend
        return DatabaseSearchBackend(params)
