import logging

from django.http.request import validate_host

logger = logging.getLogger("wagtail.frontendcache")


__all__ = ["BaseBackend"]


class BaseBackend:
    def __init__(self, params):
        # If unspecified, invalidate all hosts
        self.hostnames = params.get("HOSTNAMES", ["*"])

    def purge(self, url) -> None:
        raise NotImplementedError

    def purge_batch(self, urls) -> None:
        # Fallback for backends that do not support batch purging
        for url in urls:
            self.purge(url)

    def invalidates_hostname(self, hostname) -> bool:
        """
        Can `hostname` be invalidated by this backend?
        """
        return validate_host(hostname, self.hostnames)
