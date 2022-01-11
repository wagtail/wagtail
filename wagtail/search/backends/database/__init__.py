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
        from .sqlite.utils import fts5_available
        if fts5_available():
            from .sqlite.sqlite import SQLiteSearchBackend
            return SQLiteSearchBackend(params)
        else:
            from .fallback import DatabaseSearchBackend
            return DatabaseSearchBackend(params)
    else:
        from .fallback import DatabaseSearchBackend
        return DatabaseSearchBackend(params)
