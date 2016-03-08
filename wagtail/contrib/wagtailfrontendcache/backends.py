from __future__ import absolute_import, unicode_literals

import boto3
import botocore
import json
import logging
import uuid
import six

from django.core.exceptions import ImproperlyConfigured
from django.utils.six.moves.urllib.error import HTTPError, URLError
from django.utils.six.moves.urllib.parse import urlparse, urlunparse, urlencode
from django.utils.six.moves.urllib.request import Request, urlopen

from wagtail.wagtailcore import __version__

logger = logging.getLogger('wagtail.frontendcache')


class PurgeRequest(Request):
    def get_method(self):
        return 'PURGE'


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

        request = PurgeRequest(
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
            }
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


class CloudfrontBackend(BaseBackend):
    def __init__(self, params):
        self.client = boto3.client('cloudfront')
        try:
            self.cloudfront_distribution_id = params.pop('DISTRIBUTION_ID')
        except KeyError:
            raise ImproperlyConfigured(
                "The setting 'WAGTAILFRONTENDCACHE' requires the object "
                "'DISTRIBUTION_ID'."
            )

    def purge(self, url):
        try:
            url_parsed = urlparse(url)
            path = url_parsed.path
            self.client.create_invalidation(
                DistributionId=self.cloudfront_distribution_id,
                InvalidationBatch={
                    'Paths': {
                        'Quantity': 1,
                        'Items': [
                            path,
                        ]
                    },
                    'CallerReference': str(uuid.uuid4())
                }
            )
        except botocore.exceptions.ClientError as e:
            logger.error("Couldn't purge '%s' from Cloudfront. ClientError: %s %s", path, e.response['Error']['Code'], e.response['Error']['Message'])
