import logging
from urllib.parse import urlsplit, urlunsplit

from django.core.exceptions import ImproperlyConfigured

from .base import BaseBackend

logger = logging.getLogger("wagtail.frontendcache")


__all__ = ["AzureBaseBackend", "AzureFrontDoorBackend", "AzureCdnBackend"]


class AzureBaseBackend(BaseBackend):
    def __init__(self, params):
        super().__init__(params)
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
            "content_paths": set(paths),
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


class AzureFrontDoorBackend(AzureBaseBackend):
    def __init__(self, params):
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

        return kwargs

    def _make_purge_call(self, client, paths):
        return client.endpoints.purge_content(
            **self._get_purge_kwargs(paths),
            front_door_name=self._front_door_name,
        )


class AzureCdnBackend(AzureBaseBackend):
    def __init__(self, params):
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

        return kwargs

    def _make_purge_call(self, client, paths):
        return client.endpoints.purge_content(
            **self._get_purge_kwargs(paths),
            profile_name=self._cdn_profile_name,
            endpoint_name=self._cdn_endpoint_name,
        )
