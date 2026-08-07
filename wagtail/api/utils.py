from urllib.parse import urlsplit

from django.conf import settings
from django.utils.encoding import force_str

from wagtail.models import Site


def get_base_url(request=None):
    base_url = getattr(settings, "WAGTAILAPI_BASE_URL", None)

    if base_url is None and request:
        site = Site.find_for_request(request)
        if site:
            base_url = site.root_url

    if base_url:
        # We only want the scheme and netloc
        base_url_parsed = urlsplit(force_str(base_url))

        return base_url_parsed.scheme + "://" + base_url_parsed.netloc

    return None


def get_full_url(request, path):
    if path.startswith(("http://", "https://")):
        return path
    base_url = get_base_url(request) or ""
    return base_url + path
