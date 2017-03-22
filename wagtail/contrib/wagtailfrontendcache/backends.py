from __future__ import absolute_import, unicode_literals

import logging
import uuid

import requests
from django.core.exceptions import ImproperlyConfigured
from django.utils.six.moves.urllib.error import HTTPError, URLError
from django.utils.six.moves.urllib.parse import urlparse, urlunparse
from django.utils.six.moves.urllib.request import Request, urlopen

from wagtail import __version__

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
        self.cloudflare_zoneid = params.pop('ZONEID')

    def purge(self, url):
        try:
            purge_url = 'https://api.cloudflare.com/client/v4/zones/{0}/purge_cache'.format(self.cloudflare_zoneid)

            headers = {
                "X-Auth-Email": self.cloudflare_email,
                "X-Auth-Key": self.cloudflare_token,
                "Content-Type": "application/json",
            }

            data = {"files": [url]}

            response = requests.delete(
                purge_url,
                json=data,
                headers=headers,
            )

            try:
                response_json = response.json()
            except ValueError:
                if response.status_code != 200:
                    response.raise_for_status()
                else:
                    logger.error("Couldn't purge '%s' from Cloudflare. Unexpected JSON parse error.", url)

        except requests.exceptions.HTTPError as e:
            logger.error("Couldn't purge '%s' from Cloudflare. HTTPError: %d %s", url, e.response.status_code, e.message)
            return
        except requests.exceptions.InvalidURL as e:
            logger.error("Couldn't purge '%s' from Cloudflare. URLError: %s", url, e.message)
            return

        if response_json['success'] is False:
            error_messages = ', '.join([str(err['message']) for err in response_json['errors']])
            logger.error("Couldn't purge '%s' from Cloudflare. Cloudflare errors '%s'", url, error_messages)
            return


class CloudfrontBackend(BaseBackend):
    def __init__(self, params):
        import boto3

        self.client = boto3.client('cloudfront')
        try:
            self.cloudfront_distribution_id = params.pop('DISTRIBUTION_ID')
        except KeyError:
            raise ImproperlyConfigured(
                "The setting 'WAGTAILFRONTENDCACHE' requires the object 'DISTRIBUTION_ID'."
            )

    def purge(self, url):
        url_parsed = urlparse(url)
        distribution_id = None

        if isinstance(self.cloudfront_distribution_id, dict):
            host = url_parsed.hostname
            if host in self.cloudfront_distribution_id:
                distribution_id = self.cloudfront_distribution_id.get(host)
            else:
                logger.info(
                    "Couldn't purge '%s' from CloudFront. Hostname '%s' not found in the DISTRIBUTION_ID mapping",
                    url, host)
        else:
            distribution_id = self.cloudfront_distribution_id

        if distribution_id:
            path = url_parsed.path
            self._create_invalidation(distribution_id, path)

    def _create_invalidation(self, distribution_id, path):
        import botocore

        try:
            self.client.create_invalidation(
                DistributionId=distribution_id,
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
            logger.error(
                "Couldn't purge '%s' from CloudFront. ClientError: %s %s", path, e.response['Error']['Code'],
                e.response['Error']['Message'])
