import logging

try:
    from importlib import import_module
except ImportError:
    # for Python 2.6, fall back on django.utils.importlib (deprecated as of Django 1.7)
    from django.utils.importlib import import_module

import sys

from django.utils import six
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


logger = logging.getLogger('wagtail.frontendcache')


class InvalidFrontendCacheBackendError(ImproperlyConfigured):
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


def get_backends(backend_settings=None, backends=None):
    # Get backend settings from WAGTAILFRONTENDCACHE setting
    if backend_settings is None:
        backend_settings = getattr(settings, 'WAGTAILFRONTENDCACHE', None)

    # Fallback to using WAGTAILFRONTENDCACHE_LOCATION setting (backwards compatibility)
    if backend_settings is None:
        cache_location = getattr(settings, 'WAGTAILFRONTENDCACHE_LOCATION', None)

        if cache_location is not None:
            backend_settings = {
                'default': {
                    'BACKEND': 'wagtail.contrib.wagtailfrontendcache.backends.HTTPBackend',
                    'LOCATION': cache_location,
                },
            }

    # No settings found, return empty list
    if backend_settings is None:
        return {}

    backend_objects = {}

    for backend_name, _backend_config in backend_settings.items():
        if backends is not None and backend_name not in backends:
            continue

        backend_config = _backend_config.copy()
        backend = backend_config.pop('BACKEND')

        # Try to import the backend
        try:
            backend_cls = import_string(backend)
        except ImportError as e:
            raise InvalidFrontendCacheBackendError("Could not find backend '%s': %s" % (
                backend, e))

        backend_objects[backend_name] = backend_cls(backend_config)

    return backend_objects


def purge_url_from_cache(url, backend_settings=None, backends=None): 
    for backend_name, backend in get_backends(backend_settings=backend_settings, backends=backends).items():
        logger.info("[%s] Purging URL: %s", backend_name, url)
        backend.purge(url)


def purge_page_from_cache(page, backend_settings=None, backends=None):
    for backend_name, backend in get_backends(backend_settings=backend_settings, backends=backends).items():
        # Purge cached paths from cache
        for path in page.specific.get_cached_paths():
            logger.info("[%s] Purging URL: %s", backend_name, page.full_url + path[1:])
            backend.purge(page.full_url + path[1:])
