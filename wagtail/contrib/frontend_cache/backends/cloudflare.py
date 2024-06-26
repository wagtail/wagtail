import logging

import requests
from django.core.exceptions import ImproperlyConfigured

from .base import BaseBackend

logger = logging.getLogger("wagtail.frontendcache")


__all__ = ["CloudflareBackend"]


class CloudflareBackend(BaseBackend):
    CHUNK_SIZE = 30

    def __init__(self, params):
        super().__init__(params)

        self.cloudflare_email = params.pop("EMAIL", None)
        self.cloudflare_api_key = params.pop("TOKEN", None) or params.pop(
            "API_KEY", None
        )
        self.cloudflare_token = params.pop("BEARER_TOKEN", None)
        self.cloudflare_zoneid = params.pop("ZONEID")
        self.cloudflare_purge_endpoint_url = (
            "https://api.cloudflare.com/client/v4/zones/{}/purge_cache".format(
                self.cloudflare_zoneid
            )
        )

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
                "https://api.cloudflare.com/client/v4/zones/{}/purge_cache".format(
                    self.cloudflare_zoneid
                )
            )

            headers = {"Content-Type": "application/json"}

            if self.cloudflare_token:
                headers["Authorization"] = f"Bearer {self.cloudflare_token}"
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
        self._purge_urls([url])
