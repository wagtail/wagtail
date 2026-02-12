import logging
import re
from collections import defaultdict
from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from django_tasks import task

from wagtail.coreutils import get_content_languages

from .utils import get_backends

logger = logging.getLogger("wagtail.frontendcache")


@task()
def purge_urls_from_cache_task(urls, backend_settings=None, backends=None):
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
