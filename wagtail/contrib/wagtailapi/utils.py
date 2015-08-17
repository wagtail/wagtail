from django.conf import settings
from django.utils.six.moves.urllib.parse import urlparse

from wagtail.wagtailcore.models import Page


class BadRequestError(Exception):
    pass


class URLPath(object):
    """
    This class represents a URL path that should be converted to a full URL.

    It is used when the domain that should be used is not known at the time
    the URL was generated. It will get resolved to a full URL during
    serialisation in api.py.

    One example use case is the documents endpoint adding download URLs into
    the JSON. The endpoint does not know the domain name to use at the time so
    returns one of these instead.
    """
    def __init__(self, path):
        self.path = path


class ObjectDetailURL(object):
    def __init__(self, model, pk):
        self.model = model
        self.pk = pk


def get_base_url(request=None):
    base_url = getattr(settings, 'WAGTAILAPI_BASE_URL', request.site.root_url if request else None)

    if base_url:
        # We only want the scheme and netloc
        base_url_parsed = urlparse(base_url)

        return base_url_parsed.scheme + '://' + base_url_parsed.netloc


def pages_for_site(site):
    pages = Page.objects.public().live()
    pages = pages.descendant_of(site.root_page, inclusive=True)
    return pages
