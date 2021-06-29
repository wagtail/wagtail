from .fallback import DatabaseSearchBackend


def SearchBackend(params):
    """
    Returns the appropriate search backend for the current 'default' database system
    """
    return DatabaseSearchBackend(params)
