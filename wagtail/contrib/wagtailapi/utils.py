from six.moves.urllib.parse import urlparse

from django.conf import settings


class BadRequestError(Exception):
    pass


def get_base_url(request=None):
    base_url = getattr(settings, 'WAGTAILAPI_BASE_URL', request.site.root_url if request else None)

    if base_url:
        # We only want the scheme and netloc
        base_url_parsed = urlparse(base_url)

        return base_url_parsed.scheme + '://' + base_url_parsed.netloc
