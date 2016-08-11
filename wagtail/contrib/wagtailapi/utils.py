from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.utils.six.moves.urllib.parse import urlparse

from wagtail.wagtailcore.models import Page


class BadRequestError(Exception):
    pass


def get_base_url(request=None):
    base_url = getattr(settings, 'WAGTAILAPI_BASE_URL', request.site.root_url if request else None)

    if base_url:
        # We only want the scheme and netloc
        base_url_parsed = urlparse(base_url)

        return base_url_parsed.scheme + '://' + base_url_parsed.netloc


def get_full_url(request, path):
    base_url = get_base_url(request) or ''
    return base_url + path


def pages_for_site(site):
    pages = Page.objects.public().live()
    pages = pages.descendant_of(site.root_page, inclusive=True)
    return pages
