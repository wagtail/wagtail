from urlparse import urlparse, urlunparse
import requests

from django.conf import settings


def purge_page_from_cache(page):
    # Build purge url
    varnish_url = urlparse(getattr(settings, 'WAGTAILFRONTENDCACHE_LOCATION', 'http://127.0.0.1:8000/'))
    page_url = urlparse(page.url)
    purge_url = urlunparse((varnish_url.scheme, varnish_url.netloc, page_url.path, page_url.params, page_url.query, page_url.fragment))

    # Purge
    requests.request('PURGE', purge_url)
