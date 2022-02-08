# Backend loading
# Based on the Django cache framework
# https://github.com/django/django/blob/5d263dee304fdaf95e18d2f0619d6925984a7f02/django/core/cache/__init__.py

from importlib import import_module

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string


class InvalidSearchBackendError(ImproperlyConfigured):
    pass


def get_search_backend_config():
    search_backends = getattr(settings, 'WAGTAILSEARCH_BACKENDS', {})

    # Make sure the default backend is always defined
    search_backends.setdefault('default', {
        'BACKEND': 'wagtail.search.backends.database',
    })

    return search_backends


def import_backend(dotted_path):
    """
    There's two formats for the dotted_path.
    One with the backend class (old) and one without (new)
    eg:
      old: wagtail.search.backends.elasticsearch.ElasticsearchSearchBackend
      new: wagtail.search.backends.elasticsearch

    If a new style dotted path was specified, this function would
    look for a backend class from the "SearchBackend" attribute.
    """
    try:
        # New
        backend_module = import_module(dotted_path)
        return backend_module.SearchBackend
    except ImportError as e:
        try:
            # Old
            return import_string(dotted_path)
        except ImportError:
            raise ImportError from e


def get_search_backend(backend='default', **kwargs):
    search_backends = get_search_backend_config()

    # Try to find the backend
    try:
        # Try to get the WAGTAILSEARCH_BACKENDS entry for the given backend name first
        conf = search_backends[backend]
    except KeyError:
        try:
            # Trying to import the given backend, in case it's a dotted path
            import_backend(backend)
        except ImportError as e:
            raise InvalidSearchBackendError("Could not find backend '%s': %s" % (
                backend, e))
        params = kwargs
    else:
        # Backend is a conf entry
        params = conf.copy()
        params.update(kwargs)
        backend = params.pop('BACKEND')

    # Try to import the backend
    try:
        backend_cls = import_backend(backend)
    except ImportError as e:
        raise InvalidSearchBackendError("Could not find backend '%s': %s" % (
            backend, e))

    # Create backend
    return backend_cls(params)


def _backend_requires_auto_update(backend_name, params):
    if params.get('AUTO_UPDATE', True):
        return True

    # _WAGTAILSEARCH_FORCE_AUTO_UPDATE is only used by Wagtail tests. It allows
    # us to test AUTO_UPDATE behaviour against Elasticsearch without having to
    # have AUTO_UPDATE enabed for every test.
    force_auto_update = getattr(settings, '_WAGTAILSEARCH_FORCE_AUTO_UPDATE', [])
    if backend_name in force_auto_update:
        return True

    return False


def get_search_backends_with_name(with_auto_update=False):
    search_backends = get_search_backend_config()
    for backend, params in search_backends.items():
        if with_auto_update and _backend_requires_auto_update(backend, params) is False:
            continue

        yield backend, get_search_backend(backend)


def get_search_backends(with_auto_update=False):
    # For backwards compatibility
    return (backend for _, backend in get_search_backends_with_name(with_auto_update=with_auto_update))
