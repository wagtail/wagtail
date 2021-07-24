from django.db import connection


def SearchBackend(params):
    """
    Returns the appropriate search backend for the current 'default' database system
    """
    if connection.vendor == 'postgresql':
        from .postgres.postgres import PostgresSearchBackend
        return PostgresSearchBackend(params)
    if connection.vendor == 'sqlite':
        from .sqlite.sqlite import SQLiteSearchBackend
        return SQLiteSearchBackend(params)
    else:
        from .fallback import DatabaseSearchBackend
        return DatabaseSearchBackend(params)
