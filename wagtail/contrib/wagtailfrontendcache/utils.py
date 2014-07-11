import requests
from requests.adapters import HTTPAdapter

from django.conf import settings


class CustomHTTPAdapter(HTTPAdapter):
    """
    Requests will always send requests to whatever server is in the netloc
    part of the URL. This is a problem with purging the cache as this netloc
    may point to a different server (such as an nginx instance running in
    front of the cache).

    This class allows us to send a purge request directly to the cache server
    with the host header still set correctly. It does this by changing the "url"
    parameter of get_connection to always point to the cache server. Requests
    will then use this connection to purge the page.
    """
    def __init__(self, cache_url):
        self.cache_url = cache_url
        super(CustomHTTPAdapter, self).__init__()

    def get_connection(self, url, proxies=None):
        return super(CustomHTTPAdapter, self).get_connection(self.cache_url, proxies)


def purge_url_from_cache(url):
    # Get session
    cache_server_url = getattr(settings, 'WAGTAILFRONTENDCACHE_LOCATION', 'http://127.0.0.1:8000/')
    session = requests.Session()
    session.mount('http://', CustomHTTPAdapter(cache_server_url))

    # Send purge request to cache
    session.request('PURGE', url)


def purge_page_from_cache(page):
    # Purge cached paths from cache
    for path in page.specific.get_cached_paths():
        purge_url_from_cache(page.full_url + path[1:])
