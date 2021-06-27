from django.db import connection

from .fallback import DatabaseSearchBackend
from .postgres import PostgresSearchBackend


def SearchBackend(params):
    """
    Returns the appropriate search backend for the current 'default' database system
    """
    if connection.vendor == 'postgresql':
        return PostgresSearchBackend(params)
    else:
        return DatabaseSearchBackend(params)
