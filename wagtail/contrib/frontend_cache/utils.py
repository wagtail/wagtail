import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

logger = logging.getLogger("wagtail.frontendcache")


class InvalidFrontendCacheBackendError(ImproperlyConfigured):
    pass


def get_backends(backend_settings=None, backends=None):
    # Get backend settings from WAGTAILFRONTENDCACHE setting
    if backend_settings is None:
        backend_settings = getattr(settings, "WAGTAILFRONTENDCACHE", None)

    # Fallback to using WAGTAILFRONTENDCACHE_LOCATION setting (backwards compatibility)
    if backend_settings is None:
        cache_location = getattr(settings, "WAGTAILFRONTENDCACHE_LOCATION", None)

        if cache_location is not None:
            backend_settings = {
                "default": {
                    "BACKEND": "wagtail.contrib.frontend_cache.backends.HTTPBackend",
                    "LOCATION": cache_location,
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
        backend = backend_config.pop("BACKEND")

        # Try to import the backend
        try:
            backend_cls = import_string(backend)
        except ImportError as e:
            raise InvalidFrontendCacheBackendError(
                f"Could not find backend '{backend}': {e}"
            )

        backend_objects[backend_name] = backend_cls(backend_config)

    return backend_objects


def purge_url_from_cache(url, backend_settings=None, backends=None):
    purge_urls_from_cache([url], backend_settings=backend_settings, backends=backends)


def purge_urls_from_cache(urls, backend_settings=None, backends=None):
    from .tasks import purge_urls_from_cache_task

    purge_urls_from_cache_task.enqueue(list(urls), backend_settings, backends)


def _get_page_cached_urls(page):
    page_url = page.full_url
    if page_url is None:  # nothing to be done if the page has no routable URL
        return []

    return [page_url + path.lstrip("/") for path in page.specific.get_cached_paths()]


def purge_page_from_cache(page, backend_settings=None, backends=None):
    purge_pages_from_cache([page], backend_settings=backend_settings, backends=backends)


def purge_pages_from_cache(pages, backend_settings=None, backends=None):
    urls = []
    for page in pages:
        urls.extend(_get_page_cached_urls(page))

    if urls:
        purge_urls_from_cache(urls, backend_settings, backends)


class PurgeBatch:
    """Represents a list of URLs to be purged in a single request"""

    def __init__(self, urls=None):
        self.urls = set()

        if urls is not None:
            self.add_urls(urls)

    def add_url(self, url):
        """Adds a single URL"""
        self.urls.add(url)

    def add_urls(self, urls):
        """
        Adds multiple URLs from an iterable

        This is equivalent to running ``.add_url(url)`` on each URL
        individually
        """
        self.urls.update(urls)

    def add_page(self, page):
        """
        Adds all URLs for the specified page

        This combines the page's full URL with each path that is returned by
        the page's `.get_cached_paths` method
        """
        self.add_urls(_get_page_cached_urls(page))

    def add_pages(self, pages):
        """
        Adds multiple pages from a QuerySet or an iterable

        This is equivalent to running ``.add_page(page)`` on each page
        individually
        """
        for page in pages:
            self.add_page(page)

    def purge(self, backend_settings=None, backends=None):
        """
        Performs the purge of all the URLs in this batch

        This method takes two optional keyword arguments: backend_settings and backends

        - backend_settings can be used to override the WAGTAILFRONTENDCACHE setting for
          just this call

        - backends can be set to a list of backend names. When set, the invalidation request
          will only be sent to these backends
        """
        purge_urls_from_cache(self.urls, backend_settings, backends)
