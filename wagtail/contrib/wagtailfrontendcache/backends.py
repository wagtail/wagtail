import logging
import json

from django.utils.six.moves.urllib.parse import urlparse, urlunparse, urlencode
from django.utils.six.moves.urllib.request import Request, urlopen
from django.utils.six.moves.urllib.error import URLError, HTTPError

from wagtail.wagtailcore import __version__


logger = logging.getLogger('wagtail.frontendcache')


class BaseBackend(object):
    def purge(self, url):
        raise NotImplementedError


class HTTPBackend(BaseBackend):
    def __init__(self, params):
        location_url_parsed = urlparse(params.pop('LOCATION'))
        self.cache_scheme = location_url_parsed.scheme
        self.cache_netloc = location_url_parsed.netloc

    def purge(self, url):
        url_parsed = urlparse(url)
        host = url_parsed.hostname

        # Append port to host if it is set in the original URL
        if url_parsed.port:
            host += (':' + str(url_parsed.port))

        request = Request(
            url=urlunparse([
                self.cache_scheme,
                self.cache_netloc,
                url_parsed.path,
                url_parsed.params,
                url_parsed.query,
                url_parsed.fragment
            ]),
            headers={
                'Host': host,
                'User-Agent': 'Wagtail-frontendcache/' + __version__
            },
            method='PURGE'
        )

        try:
            urlopen(request)
        except HTTPError as e:
            logger.error("Couldn't purge '%s' from HTTP cache. HTTPError: %d %s", url, e.code, e.reason)
        except URLError as e:
            logger.error("Couldn't purge '%s' from HTTP cache. URLError: %s", url, e.reason)


class CloudflareBackend(BaseBackend):
    def __init__(self, params):
        self.cloudflare_email = params.pop('EMAIL')
        self.cloudflare_token = params.pop('TOKEN')

    def purge(self, url):
        try:
            response = urlopen('https://www.cloudflare.com/api_json.html', data=urlencode({
                'email': self.cloudflare_email,
                'tkn': self.cloudflare_token,
                'a': 'zone_file_purge',
                'z': urlparse(url).netloc,
                'url': url
            }).encode('utf-8'))
        except HTTPError as e:
            logger.error("Couldn't purge '%s' from Cloudflare. HTTPError: %d %s", url, e.code, e.reason)
            return
        except URLError as e:
            logger.error("Couldn't purge '%s' from Cloudflare. URLError: %s", url, e.reason)
            return

        response_json = json.loads(response.read().decode('utf-8'))
        if response_json['result'] == 'error':
            logger.error("Couldn't purge '%s' from Cloudflare. Cloudflare error '%s'", url, response_json['msg'])
            return
