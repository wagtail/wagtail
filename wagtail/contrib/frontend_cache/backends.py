import logging
import uuid
import warnings
from collections import defaultdict
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urlsplit, urlunparse, urlunsplit
from urllib.request import Request, urlopen

import requests
from django.core.exceptions import ImproperlyConfigured

from wagtail import __version__
from wagtail.utils.deprecation import RemovedInWagtail50Warning

logger = logging.getLogger("wagtail.frontendcache")


class PurgeRequest(Request):
    def get_method(self):
        return "PURGE"


class BaseBackend:
    def purge(self, url):
        raise NotImplementedError

    def purge_batch(self, urls):
        # Fallback for backends that do not support batch purging
        for url in urls:
            self.purge(url)


class HTTPBackend(BaseBackend):
    def __init__(self, params):
        location_url_parsed = urlparse(params.pop("LOCATION"))
        self.cache_scheme = location_url_parsed.scheme
        self.cache_netloc = location_url_parsed.netloc

    def purge(self, url):
        url_parsed = urlparse(url)
        host = url_parsed.hostname

        # Append port to host if it is set in the original URL
        if url_parsed.port:
            host += ":" + str(url_parsed.port)

        request = PurgeRequest(
            url=urlunparse(
                [
                    self.cache_scheme,
                    self.cache_netloc,
                    url_parsed.path,
                    url_parsed.params,
                    url_parsed.query,
                    url_parsed.fragment,
                ]
            ),
            headers={
                "Host": host,
                "User-Agent": "Wagtail-frontendcache/" + __version__,
            },
        )

        try:
            urlopen(request)
        except HTTPError as e:
            logger.error(
                "Couldn't purge '%s' from HTTP cache. HTTPError: %d %s",
                url,
                e.code,
                e.reason,
            )
        except URLError as e:
            logger.error(
                "Couldn't purge '%s' from HTTP cache. URLError: %s", url, e.reason
            )


class CloudflareBackend(BaseBackend):
    CHUNK_SIZE = 30

    def __init__(self, params):
        self.cloudflare_email = params.pop("EMAIL", None)
        self.cloudflare_api_key = params.pop("TOKEN", None) or params.pop(
            "API_KEY", None
        )
        self.cloudflare_token = params.pop("BEARER_TOKEN", None)
        self.cloudflare_zoneid = params.pop("ZONEID")

        if (
            (not self.cloudflare_email and self.cloudflare_api_key)
            or (self.cloudflare_email and not self.cloudflare_api_key)
            or (
                not any(
                    [
                        self.cloudflare_email,
                        self.cloudflare_api_key,
                        self.cloudflare_token,
                    ]
                )
            )
        ):
            raise ImproperlyConfigured(
                "The setting 'WAGTAILFRONTENDCACHE' requires both 'EMAIL' and 'API_KEY', or 'BEARER_TOKEN' to be specified."
            )

    def _purge_urls(self, urls):
        try:
            purge_url = (
                "https://api.cloudflare.com/client/v4/zones/{0}/purge_cache".format(
                    self.cloudflare_zoneid
                )
            )

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
                        logger.error(
                            "Couldn't purge '%s' from Cloudflare. Unexpected JSON parse error.",
                            url,
                        )

        except requests.exceptions.HTTPError as e:
            for url in urls:
                logging.exception(
                    "Couldn't purge '%s' from Cloudflare. HTTPError: %d",
                    url,
                    e.response.status_code,
                )
            return

        if response_json["success"] is False:
            error_messages = ", ".join(
                [str(err["message"]) for err in response_json["errors"]]
            )
            for url in urls:
                logger.error(
                    "Couldn't purge '%s' from Cloudflare. Cloudflare errors '%s'",
                    url,
                    error_messages,
                )
            return

    def purge_batch(self, urls):
        # Break the batched URLs in to chunks to fit within Cloudflare's maximum size for
        # the purge_cache call (https://api.cloudflare.com/#zone-purge-files-by-url)
        for i in range(0, len(urls), self.CHUNK_SIZE):
            chunk = urls[i : i + self.CHUNK_SIZE]
            self._purge_urls(chunk)

    def purge(self, url):
        self.purge_batch([url])


class CloudfrontBackend(BaseBackend):
    def __init__(self, params):
        import boto3

        self.client = boto3.client("cloudfront")
        try:
            self.cloudfront_distribution_id = params.pop("DISTRIBUTION_ID")
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
                        url,
                        host,
                    )
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
                    "Paths": {"Quantity": len(paths), "Items": paths},
                    "CallerReference": str(uuid.uuid4()),
                },
            )
        except botocore.exceptions.ClientError as e:
            for path in paths:
                logger.error(
                    "Couldn't purge path '%s' from CloudFront (DistributionId=%s). ClientError: %s %s",
                    path,
                    distribution_id,
                    e.response["Error"]["Code"],
                    e.response["Error"]["Message"],
                )


class AzureBaseBackend(BaseBackend):
    def __init__(self, params):
        self._credentials = params.pop("CREDENTIALS", None)
        self._subscription_id = params.pop("SUBSCRIPTION_ID", None)
        try:
            self._resource_group_name = params.pop("RESOURCE_GROUP_NAME")
        except KeyError:
            raise ImproperlyConfigured(
                "The setting 'WAGTAILFRONTENDCACHE' requires 'RESOURCE_GROUP_NAME' to be specified."
            )
        self._custom_headers = params.pop("CUSTOM_HEADERS", None)

    def purge_batch(self, urls):
        self._purge_content([self._get_path(url) for url in urls])

    def purge(self, url):
        self.purge_batch([url])

    def _get_default_credentials(self):
        try:
            from azure.identity import DefaultAzureCredential
        except ImportError:
            return
        return DefaultAzureCredential()

    def _get_credentials(self):
        """
        Use credentials object set by user. If not set, use the one configured
        in the current environment.
        """
        user_credentials = self._credentials
        if user_credentials:
            return user_credentials
        return self._get_default_credentials()

    def _get_default_subscription_id(self):
        """
        Obtain subscription ID directly from Azure.
        """
        try:
            from azure.mgmt.resource import SubscriptionClient
        except ImportError:
            return ""
        credential = self._get_credentials()
        subscription_client = SubscriptionClient(credential)
        subscription = next(subscription_client.subscriptions.list())
        return subscription.subscription_id

    def _get_subscription_id(self):
        """
        Use subscription ID set in the user configuration. If not set, try to
        retrieve one from Azure directly.
        """
        user_subscription_id = self._subscription_id
        if user_subscription_id:
            return user_subscription_id
        return self._get_default_subscription_id()

    def _get_client_kwargs(self):
        return {
            "credential": self._get_credentials(),
            "subscription_id": self._get_subscription_id(),
        }

    def _get_path(self, url):
        """
        Split netloc from the URL and return path only.
        """
        # Delete scheme and netloc from the URL, that will result in only path being
        # left.
        url_parts = ("",) * 2 + urlsplit(url)[2:]
        return urlunsplit(url_parts)

    def _get_client(self):
        """
        Get Azure client instance.
        """
        klass = self._get_client_class()
        kwargs = self._get_client_kwargs()
        return klass(**kwargs)

    def _get_purge_kwargs(self, paths):
        """
        Get keyword arguments passes to Azure purge content calls.
        """
        return {
            "resource_group_name": self._resource_group_name,
            "custom_headers": self._custom_headers,
            "content_paths": paths,
        }

    def _purge_content(self, paths):
        from msrest.exceptions import HttpOperationError

        client = self._get_client()
        try:
            self._make_purge_call(client, paths)
        except HttpOperationError as exception:
            for path in paths:
                logger.exception(
                    "Couldn't purge '%s' from %s cache. HttpOperationError: %r",
                    path,
                    type(self).__name__,
                    exception.response,
                )

    def _is_legacy_azure_library(self, *, major_required, installed_version):
        """
        Return `True` if the major part of the parsed `installed_version` string is
        smaller than `major_required`.

        This code is used to check versions from Azure libraries that got a backwards
        incompatible change in versions 10 (azure-mgmt-cdn) and 1.0
        (azure-mgmt-frontdoor).
        """
        try:
            major = int(installed_version.split(".", maxsplit=1)[0])
        except (IndexError, ValueError):
            return False

        return major < major_required


class AzureFrontDoorBackend(AzureBaseBackend):
    def __init__(self, params):
        from azure.mgmt.frontdoor import __version__

        self._legacy_azure_library = self._is_legacy_azure_library(
            major_required=1, installed_version=__version__
        )

        if self._legacy_azure_library:
            warnings.warn(
                f"Support for azure-mgmt-frontdoor {__version__} will be dropped in the next release. Please upgrade to azure-mgmt-frontdoor >= 1.0.",
                RemovedInWagtail50Warning,
            )

        super().__init__(params)
        try:
            self._front_door_name = params.pop("FRONT_DOOR_NAME")
        except KeyError:
            raise ImproperlyConfigured(
                "The setting 'WAGTAILFRONTENDCACHE' requires 'FRONT_DOOR_NAME' to be specified."
            )
        self._front_door_service_url = params.pop("FRONT_DOOR_SERVICE_URL", None)

    def _get_client_class(self):
        from azure.mgmt.frontdoor import FrontDoorManagementClient

        return FrontDoorManagementClient

    def _get_client_kwargs(self):
        kwargs = super()._get_client_kwargs()
        kwargs.setdefault("base_url", self._front_door_service_url)

        if self._legacy_azure_library:
            kwargs["credentials"] = kwargs.pop("credential")

        return kwargs

    def _make_purge_call(self, client, paths):
        return client.endpoints.purge_content(
            **self._get_purge_kwargs(paths),
            front_door_name=self._front_door_name,
        )


class AzureCdnBackend(AzureBaseBackend):
    def __init__(self, params):
        from azure.mgmt.cdn import __version__

        self._legacy_azure_library = self._is_legacy_azure_library(
            major_required=10, installed_version=__version__
        )

        if self._legacy_azure_library:
            warnings.warn(
                f"Support for azure-mgmt-cdn {__version__} will be dropped in the next release. Please upgrade to azure-mgmt-cdn >= 10.",
                RemovedInWagtail50Warning,
            )

        super().__init__(params)
        try:
            self._cdn_profile_name = params.pop("CDN_PROFILE_NAME")
            self._cdn_endpoint_name = params.pop("CDN_ENDPOINT_NAME")
        except KeyError:
            raise ImproperlyConfigured(
                "The setting 'WAGTAILFRONTENDCACHE' requires 'CDN_PROFILE_NAME' and 'CDN_ENDPOINT_NAME' to be specified."
            )
        self._cdn_service_url = params.pop("CDN_SERVICE_URL", None)

    def _get_client_class(self):
        from azure.mgmt.cdn import CdnManagementClient

        return CdnManagementClient

    def _get_client_kwargs(self):
        kwargs = super()._get_client_kwargs()
        kwargs.setdefault("base_url", self._cdn_service_url)

        if self._legacy_azure_library:
            kwargs["credentials"] = kwargs.pop("credential")

        return kwargs

    def _make_purge_call(self, client, paths):
        return client.endpoints.purge_content(
            **self._get_purge_kwargs(paths),
            profile_name=self._cdn_profile_name,
            endpoint_name=self._cdn_endpoint_name,
        )
