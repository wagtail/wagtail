import hashlib

from django.conf import settings
from django.templatetags.static import static

from wagtail import __version__


if getattr(settings, 'WAGTAILADMIN_STATIC_FILE_VERSION_STRINGS', True):
    VERSION_HASH = hashlib.sha1(
        (__version__ + settings.SECRET_KEY).encode('utf-8')
    ).hexdigest()[:8]
else:
    VERSION_HASH = None


def versioned_static(path):
    """
    Wrapper for Django's static file finder to append a cache-busting query parameter
    that updates on each Wagtail version
    """
    base_url = static(path)

    # if URL already contains a querystring, don't add our own, to avoid interfering
    # with existing mechanisms
    if VERSION_HASH is None or '?' in base_url:
        return base_url
    else:
        return base_url + '?v=' + VERSION_HASH
