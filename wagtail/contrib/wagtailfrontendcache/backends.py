import logging

from six.moves.urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter


logger = logging.getLogger('wagtail.frontendcache')


class BaseBackend(object):
    def purge(self, url):
        raise NotImplementedError


class HTTPBackend(BaseBackend):

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
            super(HTTPBackend.CustomHTTPAdapter, self).__init__()

        def get_connection(self, url, proxies=None):
            return super(HTTPBackend.CustomHTTPAdapter, self).get_connection(self.cache_url, proxies)


    def __init__(self, params):
        self.cache_location = params.pop('LOCATION')

        self.session = requests.Session()
        self.session.mount('http://', self.CustomHTTPAdapter(self.cache_location))

    def purge(self, url):
        try:
            response = self.session.request('PURGE', url)
        except requests.ConnectionError:
            logger.error("Couldn't purge '%s' from HTTP cache: Connection error", url)
            return

        # Check for error
        if response.status_code != 200:
            logger.error("Couldn't purge '%s' from HTTP cache: Didn't recieve a 200 response (instead, we got '%d %s')", url, response.status_code, response.reason)
            return


class CloudflareBackend(BaseBackend):
    def __init__(self, params):
        self.cloudflare_email = params.pop('EMAIL')
        self.cloudflare_token = params.pop('TOKEN')

    def purge(self, url):
        try:
            response = requests.post('https://www.cloudflare.com/api_json.html', {
                'email': self.cloudflare_email,
                'tkn': self.cloudflare_token,
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
