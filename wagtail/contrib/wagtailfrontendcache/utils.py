import logging

from six.moves.urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter

from django.conf import settings


logger = logging.getLogger('wagtail.frontendcache')


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
    logger.info("Purging url from cache: %s", url)

    # Purge from regular cache (Varnish/Squid/etc)
    cache_server_url = getattr(settings, 'WAGTAILFRONTENDCACHE_LOCATION', None)
    if cache_server_url is not None:
        # Get session
        session = requests.Session()
        session.mount('http://', CustomHTTPAdapter(cache_server_url))

        # Send purge request to cache
        session.request('PURGE', url)

    # Purge from CloudFlare
    cloudflare_email = getattr(settings, 'WAGTAILFRONTENDCACHE_CLOUDFLARE_EMAIL', None)
    if cloudflare_email is not None:
        # Get token
        cloudflare_token = getattr(settings, 'WAGTAILFRONTENDCACHE_CLOUDFLARE_TOKEN', '')

        # Post
        try:
            response = requests.post('https://www.cloudflare.com/api_json.html', {
                'email': cloudflare_email,
                'tkn': cloudflare_token,
                'a': 'zone_file_purge',
                'z': urlparse(url).netloc,
                'url': url
            })
        except requests.ConnectionError:
            logger.error("Couldn't purge '%s' from Cloudflare: Connection error", url)
            return

        # Check for error
        if response.status_code != 200:
            logger.error("Couldn't purge '%s' from Cloudflare: Didn't recieve a 200 response (instead, we got '%d %s')", url, response.status_code, response.reason)
            return

        response_json = response.json()
        if response_json['result'] == 'error':
            logger.error("Couldn't purge '%s' from Cloudflare: Cloudflare error '%s'", url, response_json['msg'])
            return


def purge_page_from_cache(page):
    logger.info("Purging page from cache: %d (title: '%s')", page.id, page.title)

    # Purge cached paths from cache
    for path in page.specific.get_cached_paths():
        purge_url_from_cache(page.full_url + path[1:])
