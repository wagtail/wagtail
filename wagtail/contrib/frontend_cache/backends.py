import logging
import uuid

from collections import defaultdict
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, urlopen

import requests

from django.core.exceptions import ImproperlyConfigured

from wagtail import __version__


logger = logging.getLogger('wagtail.frontendcache')


class PurgeRequest(Request):
    def get_method(self):
        return 'PURGE'


class BaseBackend:
    def purge(self, url):
        raise NotImplementedError

    def purge_batch(self, urls):
        # Fallback for backends that do not support batch purging
        for url in urls:
            self.purge(url)


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
    CHUNK_SIZE = 30

    def __init__(self, params):
        self.cloudflare_email = params.pop("EMAIL", None)
        self.cloudflare_api_key = (
            params.pop("TOKEN", None)
            or params.pop("API_KEY", None)
        )
        self.cloudflare_token = params.pop("BEARER_TOKEN", None)
        self.cloudflare_zoneid = params.pop("ZONEID")

        if (
            (not self.cloudflare_email and self.cloudflare_api_key)
            or (self.cloudflare_email and not self.cloudflare_api_key)
            or (not any([self.cloudflare_email, self.cloudflare_api_key, self.cloudflare_token]))
        ):
            raise ImproperlyConfigured(
                "The setting 'WAGTAILFRONTENDCACHE' requires both 'EMAIL' and 'API_KEY', or 'BEARER_TOKEN' to be specified."
            )

    def _purge_urls(self, urls):
        try:
            purge_url = 'https://api.cloudflare.com/client/v4/zones/{0}/purge_cache'.format(self.cloudflare_zoneid)

            headers = {"Content-Type": "application/json"}

            if self.cloudflare_token:
                headers["Authorization"] = "Bearer {}".format(self.cloudflare_token)
            else:
                headers["X-Auth-Email"] = self.cloudflare_email
                headers["X-Auth-Key"] = self.cloudflare_api_key

            data = {"files": urls}

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
                    for url in urls:
                        logger.error("Couldn't purge '%s' from Cloudflare. Unexpected JSON parse error.", url)

        except requests.exceptions.HTTPError as e:
            for url in urls:
                logging.exception("Couldn't purge '%s' from Cloudflare. HTTPError: %d", url, e.response.status_code)
            return

        if response_json['success'] is False:
            error_messages = ', '.join([str(err['message']) for err in response_json['errors']])
            for url in urls:
                logger.error("Couldn't purge '%s' from Cloudflare. Cloudflare errors '%s'", url, error_messages)
            return

    def purge_batch(self, urls):
        # Break the batched URLs in to chunks to fit within Cloudflare's maximum size for
        # the purge_cache call (https://api.cloudflare.com/#zone-purge-files-by-url)
        for i in range(0, len(urls), self.CHUNK_SIZE):
            chunk = urls[i:i + self.CHUNK_SIZE]
            self._purge_urls(chunk)

    def purge(self, url):
        self.purge_batch([url])


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

    def purge_batch(self, urls):
        paths_by_distribution_id = defaultdict(list)

        for url in urls:
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
                paths_by_distribution_id[distribution_id].append(url_parsed.path)

        for distribution_id, paths in paths_by_distribution_id.items():
            self._create_invalidation(distribution_id, paths)

    def purge(self, url):
        self.purge_batch([url])

    def _create_invalidation(self, distribution_id, paths):
        import botocore

        try:
            self.client.create_invalidation(
                DistributionId=distribution_id,
                InvalidationBatch={
                    'Paths': {
                        'Quantity': len(paths),
                        'Items': paths
                    },
                    'CallerReference': str(uuid.uuid4())
                }
            )
        except botocore.exceptions.ClientError as e:
            for path in paths:
                logger.error(
                    "Couldn't purge path '%s' from CloudFront (DistributionId=%s). ClientError: %s %s",
                    path,
                    distribution_id,
                    e.response['Error']['Code'],
                    e.response['Error']['Message']
                )
