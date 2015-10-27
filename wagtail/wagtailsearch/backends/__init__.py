# Backend loading
# Based on the Django cache framework
# https://github.com/django/django/blob/5d263dee304fdaf95e18d2f0619d6925984a7f02/django/core/cache/__init__.py

import sys
from importlib import import_module

from django.utils import six
from django.utils.module_loading import import_string
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings


class InvalidSearchBackendError(ImproperlyConfigured):
    pass


def import_backend(dotted_path):
    """
    Theres two formats for the dotted_path.
    One with the backend class (old) and one without (new)
    eg:
      old: wagtail.wagtailsearch.backends.elasticsearch.ElasticSearch
      new: wagtail.wagtailsearch.backends.elasticsearch

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
            six.reraise(ImportError, e, sys.exc_info()[2])


def get_search_backend(backend='default', **kwargs):
    # Get configuration
    default_conf = {
        'default': {
            'BACKEND': 'wagtail.wagtailsearch.backends.db',
        },
    }
    WAGTAILSEARCH_BACKENDS = getattr(
        settings, 'WAGTAILSEARCH_BACKENDS', default_conf)

    # Try to find the backend
    try:
        # Try to get the WAGTAILSEARCH_BACKENDS entry for the given backend name first
        conf = WAGTAILSEARCH_BACKENDS[backend]
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


def get_search_backends(with_auto_update=False):
    if hasattr(settings, 'WAGTAILSEARCH_BACKENDS'):
        for backend, params in settings.WAGTAILSEARCH_BACKENDS.items():
            if with_auto_update and params.get('AUTO_UPDATE', True) is False:
                continue

            yield get_search_backend(backend)
    else:
        yield get_search_backend('default')
