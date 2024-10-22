import logging
import re
from collections import defaultdict
from urllib.parse import urljoin, urlsplit, urlunsplit

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

from wagtail.coreutils import get_content_languages

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
    if not urls:
        return

    backends = get_backends(backend_settings, backends)

    # If no backends are configured, there's nothing to do
    if not backends:
        return

    # Convert each url to urls one for each managed language (WAGTAILFRONTENDCACHE_LANGUAGES setting).
    # The managed languages are common to all the defined backends.
    # This depends on settings.USE_I18N
    # If WAGTAIL_I18N_ENABLED is True, this defaults to WAGTAIL_CONTENT_LANGUAGES
    wagtail_i18n_enabled = getattr(settings, "WAGTAIL_I18N_ENABLED", False)
    content_languages = get_content_languages() if wagtail_i18n_enabled else {}
    languages = getattr(
        settings, "WAGTAILFRONTENDCACHE_LANGUAGES", list(content_languages.keys())
    )
    if settings.USE_I18N and languages:
        langs_regex = "^/(%s)/" % "|".join(languages)
        new_urls = []

        # Purge the given url for each managed language
        for isocode in languages:
            for url in urls:
                up = urlsplit(url)
                new_url = urlunsplit(
                    (
                        up.scheme,
                        up.netloc,
                        re.sub(langs_regex, "/%s/" % isocode, up.path),
                        up.query,
                        up.fragment,
                    )
                )

                # Check for best performance. True if re.sub found no match
                # It happens when i18n_patterns was not used in urls.py to serve content for different languages from different URLs
                if new_url in new_urls:
                    continue

                new_urls.append(new_url)

        urls = new_urls

    urls_by_hostname = defaultdict(list)

    for url in urls:
        urls_by_hostname[urlsplit(url).netloc].append(url)

    for hostname, urls in urls_by_hostname.items():
        backends_for_hostname = {
            backend_name: backend
            for backend_name, backend in backends.items()
            if backend.invalidates_hostname(hostname)
        }

        if not backends_for_hostname:
            logger.info("Unable to find purge backend for %s", hostname)
            continue

        for backend_name, backend in backends_for_hostname.items():
            for url in urls:
                logger.info("[%s] Purging URL: %s", backend_name, url)

            backend.purge_batch(urls)


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


def purge_site(
    site,
    backend_settings=None,
    backends=None,
    url_batch_chunk_size=2000,
):
    # Classify available backends, prioritising those that are capable
    # of 'hostname-specific' purges, followed by those capabale of
    # 'everything' purges
    purge_hostname_backends = {}
    purge_all_backends = {}
    other_backends = {}
    for name, backend in get_backends(backend_settings, backends).items():
        if backend.invalidates_hostname(site.hostname):
            if backend.hostname_purge_supported():
                purge_hostname_backends[name] = backend
            elif backend.allow_everything_purge_for_hostname(site.hostname):
                purge_all_backends[name] = backend
            else:
                other_backends[name] = backend

    if not purge_hostname_backends and not purge_all_backends and not other_backends:
        logger.info("Unable to find purge backend for %s", site.hostname)
        return

    for name, backend in purge_hostname_backends.items():
        logger.info(f"Purging hostname via backend: {name}")
        backend.purge_hostname(site.hostname)

        # NOTE: We could potentially return `None` after the first purge here,
        # but there's technically nothing to stop developers registering
        # multiple backends for the same hostname, and no way for us to
        # know what is redundant, or which backend is more important

    for name, backend in purge_all_backends.items():
        # This will likely purge more than necessary, but will be more efficient
        # than cycling through every page in the tree to generate a list of URLs

        # NOTE: It is up to developers to disable 'everything' purges for
        # backends where it is too disruptive to other services
        logger.info(f"Purging everything via backend: {name}")
        backend.purge_all()

        # NOTE: We could potentially return `None` after the first purge here,
        # but there's technically nothing to stop developers registering
        # multiple backends for the same hostname, and no way for us to
        # know what is redundant, or which backend is more important

    if other_backends:
        # Count descendants
        descendant_count = site.root_page.get_descendants().count()
        logger.info(
            "Purging %d page URLs for %s",
            descendant_count,
            site.hostname,
        )
        batch = PurgeBatch()
        purge_fixed_paths_separately = False
        for i, page in enumerate(
            site.root_page.get_descendants()
            .select_related("locale")
            .specific(defer=True)
            .iterator(url_batch_chunk_size),
            start=1,
        ):
            batch.add_page(page)
            if len(batch.urls) >= url_batch_chunk_size:
                # Capture and remove any overage
                overage = batch.urls[url_batch_chunk_size:]
                batch.urls = batch.urls[:url_batch_chunk_size]
                # Purge the current batch
                batch.purge(backends=other_backends.keys())
                # Report progress
                logger.info("Progress: %d/%d", i + 1, descendant_count)
                # Start a fresh batch
                batch = PurgeBatch()
                # Add any overage to the new batch
                batch.urls = overage
                # For reporting to make sense, fixed paths must be purged separately
                purge_fixed_paths_separately = True

        if batch.urls and purge_fixed_paths_separately:
            # Purge the final batch of page urls
            batch.purge(backends=other_backends.keys())
            # Report progress
            logger.info("Progress: %d/%d", descendant_count, descendant_count)
            # Start a new batch for purging fixed paths
            batch = PurgeBatch()

        # NOTE: Add hardcoded paths/urls to the current batch
        additional_paths = getattr(
            settings, "WAGTAILFRONTENDCACHE_FIXED_SITE_PATHS", []
        )
        if additional_paths:
            logger.info(
                "Purging %d fixed site paths for %s",
                len(additional_paths),
                site.hostname,
            )
            base_url = site.root_url
            for path in additional_paths:
                batch.add_url(urljoin(base_url, path))

        batch.purge(backends=other_backends.keys())
    return


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
