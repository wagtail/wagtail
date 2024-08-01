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

    def purge_hostname(self, hostname) -> None:
        """
        Purge all cached URLs matching the provided ``hostname``. Where the underlying
        service or technology supports it, specific backends can implement this to allow
        efficient mass-purging with a minumal number of requests.

        Where not implemented, ``wagtail.contrib.frontend_cache.utils.purge_site()``
        will use ``purge_batch()`` to purge known URLs instead.
        """
        raise NotImplementedError

    def purge_everything(self) -> None:
        """
        Purge all cached URLs managed by the backend. Where the underlying service or
        technology supports it, specific backends can implement this to allow efficient
        mass-purging with a minimal number of requests.

        Where implemented (and enabled for the specific instance), this can be used by
        ``wagtail.contrib.frontend_cache.utils.purge_site()`` as an alternative to
        ``purge_hostname()``.
        """
        raise NotImplementedError

    def invalidates_hostname(self, hostname) -> bool:
        """
        Can `hostname` be invalidated by this backend?
        """
        return validate_host(hostname, self.hostnames)

    @property
    def hostname_purge_supported(self) -> bool:
        """
        Has ``purge_hostname()`` been implemented for this backend, and is the
        option enabled for this specific instance? The return value could vary,
        depending on configuration or plan restrictions.
        """
        return False

    def allow_everything_purge_for_hostname(self, hostname) -> bool:
        """
        When a request has been made to purge all URLs for supplied ``hostname``, but
        ``purge_hostname()`` is not supported by this instance, is it acceptable to purge
        'everything' instead?

        By default, this returns ``False`` because of the potential to adversely impact
        other apps or services behind the same cahe. However, it could return  ``True`` in
        cases where purging 'everything' is more-or-less equivalent to a hostname-specific
        purge. Or, on projects with huge numbers of pages, where URL-batch purges could be
        impractical.
        """
        return False
