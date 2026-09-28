"""The CDN in front of the site: the one external system Wagtail's tasks reach here."""

from collections import Counter

from wagtail.contrib.frontend_cache.backends import BaseBackend

#: Every URL the CDN was asked to purge, with how many times.
PURGED: Counter[str] = Counter()


class RecordingCDN(BaseBackend):
    """EXTERNAL SEAM: a frontend cache backend that records each purge instead of calling a CDN."""

    def purge(self, url: str) -> None:
        PURGED[url] += 1
