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
    """
    Purge a single URL from the frontend cache.

    :param url: The URL to purge from the cache.
    :type url: str
    :param backend_settings: Optional custom backend settings to use instead of those defined in ``settings.WAGTAILFRONTENDCACHE``.
    :type backend_settings: dict, optional
    :param backends: Optional list of strings referencing specific backends from ``settings.WAGTAILFRONTENDCACHE`` or provided as ``backend_settings``. Can be used to limit purge operations to specific backends.
    :type backends: list, optional

    This function purges a single URL from the configured frontend cache backends. It's useful
    when you need to invalidate the cache for a specific URL.

    If no custom backends or settings are provided, it will use the default configuration
    from ``settings.WAGTAILFRONTENDCACHE``.

    NOTE: This function also handles internationalization, creating language-specific URLs if
    ``WAGTAILFRONTENDCACHE_LANGUAGES`` is set and ``USE_I18N`` is ``True``.
    """
    purge_urls_from_cache([url], backend_settings=backend_settings, backends=backends)


def purge_urls_from_cache(urls, backend_settings=None, backends=None):
    """
    Purge multiple URLs from the frontend cache.

    :param urls: An iterable of URLs to purge from the cache.
    :type urls: iterable of str
    :param backend_settings: Optional custom backend settings to use instead of those defined in ``settings.WAGTAILFRONTENDCACHE``.
    :type backend_settings: dict, optional
    :param backends: Optional list of strings referencing specific backends from ``settings.WAGTAILFRONTENDCACHE`` or provided as ``backend_settings``. Can be used to limit purge operations to specific backends.
    :type backends: list, optional

    This function purges multiple URLs from the configured frontend cache backends. It's useful
    when you need to invalidate the cache for multiple URLs at once.

    If no custom backends or settings are provided, it will use the default configuration
    from ``settings.WAGTAILFRONTENDCACHE``.

    NOTE: This function also handles internationalization, creating language-specific URLs if
    ``WAGTAILFRONTENDCACHE_LANGUAGES`` is set and ``USE_I18N`` is ``True``.
    """
    from .tasks import purge_urls_from_cache_task

    if not urls:
        return

    purge_urls_from_cache_task.enqueue(list(urls), backend_settings, backends)


def _get_page_cached_urls(page, cache_object=None):
    page_url = page.get_full_url(cache_object)
    if page_url is None:  # nothing to be done if the page has no routable URL
        return []

    return [
        page_url + path.lstrip("/")
        for path in page.specific_deferred.get_cached_paths()
    ]


def purge_page_from_cache(
    page, backend_settings=None, backends=None, *, cache_object=None
):
    """
    Purge a single page from the frontend cache.

    :param page: The page to purge from the cache.
    :type page: Page
    :param backend_settings: Optional custom backend settings to use instead of those defined in ``settings.WAGTAILFRONTENDCACHE``.
    :type backend_settings: dict, optional
    :param backends: Optional list of strings referencing specific backends from ``settings.WAGTAILFRONTENDCACHE`` or provided as ``backend_settings``. Can be used to limit purge operations to specific backends.
    :type backends: list, optional
    :param cache_object: Optional, but strongly recommended when making a series of requests to this method. An object to be passed to URL-related methods, allowing cached site root path data to be reused across multiple requests.
    :type cache_object: object, optional

    This function retrieves all cached URLs for the given page and purges them from the configured
    backends. It's useful when you need to invalidate the cache for a specific page,
    for example after the page has been updated.

    If no custom backends or settings are provided, it will use the default configuration
    from ``settings.WAGTAILFRONTENDCACHE``.

    The `cache_object` parameter can be any kind of object that supports arbitrary attribute
    assignment, such as a Python object or Django Model instance.
    """
    urls = _get_page_cached_urls(page, cache_object)
    purge_urls_from_cache(urls, backend_settings, backends)


def purge_pages_from_cache(
    pages, backend_settings=None, backends=None, *, cache_object=None
):
    """
    Purge multiple pages from the frontend cache.

    :param pages: An iterable of pages to purge from the cache.
    :type pages: iterable of Page
    :param backend_settings: Optional custom backend settings to use instead of those defined in ``settings.WAGTAILFRONTENDCACHE``.
    :type backend_settings: dict, optional
    :param backends: Optional list of strings matching keys from ``settings.WAGTAILFRONTENDCACHE`` or provided as ``backend_settings``. Can be used to limit purge operations to specific backends.
    :type backends: list, optional
    :param cache_object: Optional object to be passed to URL-related methods, to allow cached site root path data to be reused across multiple requests to this method. If not provided, the ``PurgeBatch`` object created by this method will be used instead.
    :type cache_object: object, optional

    This function retrieves all cached URLs for the given pages and purges them from the configured
    backends. It's useful when you need to invalidate the cache for multiple pages at once,
    for example after a bulk update operation.

    If no custom backends or settings are provided, it will use the default configuration
    from ``settings.WAGTAILFRONTENDCACHE``.

    The `cache_object` parameter can be any kind of object that supports arbitrary attribute
    assignment, such as a Python object or Django Model instance.
    """
    batch = PurgeBatch(cache_object=cache_object)
    batch.add_pages(pages)
    batch.purge(backend_settings, backends)


class PurgeBatch:
    """Represents a list of URLs to be purged in a single request"""

    def __init__(self, urls=None, *, cache_object=None):
        self.urls = set()

        if urls is not None:
            self.add_urls(urls)

        self.cache_object = cache_object

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
        self.add_urls(_get_page_cached_urls(page, self.cache_object or self))

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
