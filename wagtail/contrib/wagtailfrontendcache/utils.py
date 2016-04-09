from __future__ import absolute_import, unicode_literals

import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

logger = logging.getLogger('wagtail.frontendcache')


class InvalidFrontendCacheBackendError(ImproperlyConfigured):
    pass


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
    page_url = page.full_url
    if page_url is None:  # nothing to be done if the page has no routable URL
        return

    for backend_name, backend in get_backends(backend_settings=backend_settings, backends=backends).items():
        # Purge cached paths from cache
        for path in page.specific.get_cached_paths():
            logger.info("[%s] Purging URL: %s", backend_name, page_url + path[1:])
            backend.purge(page_url + path[1:])
