import logging
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

from wagtail import __version__

from .base import BaseBackend

logger = logging.getLogger("wagtail.frontendcache")


__all__ = ["PurgeRequest", "HTTPBackend"]


class PurgeRequest(Request):
    def get_method(self):
        return "PURGE"


class HTTPBackend(BaseBackend):
    def __init__(self, params):
        super().__init__(params)
        location_url_parsed = urlsplit(params.pop("LOCATION"))
        self.cache_scheme = location_url_parsed.scheme
        self.cache_netloc = location_url_parsed.netloc

    def purge(self, url):
        url_parsed = urlsplit(url)
        host = url_parsed.hostname

        # Append port to host if it is set in the original URL
        if url_parsed.port:
            host += ":" + str(url_parsed.port)

        request = PurgeRequest(
            url=urlunsplit(
                [
                    self.cache_scheme,
                    self.cache_netloc,
                    url_parsed.path,
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
