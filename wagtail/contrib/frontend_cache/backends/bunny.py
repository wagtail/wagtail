import logging

import requests
from django.core.exceptions import ImproperlyConfigured

from .base import BaseBackend

logger = logging.getLogger("wagtail.frontendcache")


__all__ = ["BunnyBackend"]


class BunnyBackend(BaseBackend):
    PURGE_API_URL = "https://api.bunny.net/purge"

    def __init__(self, params):
        if "ACCESS_KEY" not in params:
            raise ImproperlyConfigured(
                "The Bunny backend requires ACCESS_KEY to be specified"
            )

        super().__init__(params)

        # Since Bunny's API doesn't support batch purging,
        # create a session to avoid the handshake overhead for each request.
        self.session = requests.Session()

        self.session.headers["AccessKey"] = params["ACCESS_KEY"]

    def purge(self, url):
        try:
            response = self.session.post(
                self.PURGE_API_URL, params={"url": url, "async": "true"}
            )

            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            try:
                response_json = e.response.json()
            except ValueError:
                response_json = {}

            logger.exception(
                "Couldn't purge %r from cache. HTTPError: %d. Message: %s",
                url,
                e.response.status_code,
                response_json.get("Message", ""),
            )
