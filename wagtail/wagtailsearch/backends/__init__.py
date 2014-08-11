# Backend loading
# Based on the Django cache framework
# https://github.com/django/django/blob/5d263dee304fdaf95e18d2f0619d6925984a7f02/django/core/cache/__init__.py

try:
    from importlib import import_module
except ImportError:
    # for Python 2.6, fall back on django.utils.importlib (deprecated as of Django 1.7)
    from django.utils.importlib import import_module

import sys

from django.utils import six
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class InvalidSearchBackendError(ImproperlyConfigured):
    pass


# Pinched from django 1.7 source code.
# TODO: Replace this with "from django.utils.module_loading import import_string"
# when django 1.7 is released
def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    """
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError:
        msg = "%s doesn't look like a module path" % dotted_path
        six.reraise(ImportError, ImportError(msg), sys.exc_info()[2])

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError:
        msg = 'Module "%s" does not define a "%s" attribute/class' % (
            dotted_path, class_name)
        six.reraise(ImportError, ImportError(msg), sys.exc_info()[2])


def get_search_backend(backend='default', **kwargs):
    # Get configuration
    default_conf = {
        'default': {
            'BACKEND': 'wagtail.wagtailsearch.backends.db.DBSearch',
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
            import_string(backend)
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
        backend_cls = import_string(backend)
    except ImportError as e:
        raise InvalidSearchBackendError("Could not find backend '%s': %s" % (
            backend, e))

    # Create backend
    return backend_cls(params)
