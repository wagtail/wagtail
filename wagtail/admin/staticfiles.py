import hashlib

from django.conf import settings
from django.contrib.staticfiles.storage import HashedFilesMixin
from django.core.files.storage import get_storage_class
from django.templatetags.static import static

from wagtail import __version__


# Check whether we should add cache-busting '?v=...' parameters to static file URLs
try:
    # If a preference has been explicitly stated in the WAGTAILADMIN_STATIC_FILE_VERSION_STRINGS
    # setting, use that
    use_version_strings = settings.WAGTAILADMIN_STATIC_FILE_VERSION_STRINGS
except AttributeError:
    # If WAGTAILADMIN_STATIC_FILE_VERSION_STRINGS not specified, default to version strings
    # enabled, UNLESS we're using a storage backend with hashed filenames; in this case having
    # a query parameter is redundant, and in some configurations (e.g. Cloudflare with the
    # "No Query String" setting) it could break a previously-working cache setup

    if settings.DEBUG:
        # Hashed filenames are disabled in debug mode, so keep the querystring
        use_version_strings = True
    else:
        # see if we're using a storage backend using hashed filenames
        storage = get_storage_class(settings.STATICFILES_STORAGE)
        use_version_strings = not issubclass(storage, HashedFilesMixin)


if use_version_strings:
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
    # An absolute path is returned unchanged (either a full URL, or processed already)
    if path.startswith(('http://', 'https://', '/')):
        return path

    base_url = static(path)

    # if URL already contains a querystring, don't add our own, to avoid interfering
    # with existing mechanisms
    if VERSION_HASH is None or '?' in base_url:
        return base_url
    else:
        return base_url + '?v=' + VERSION_HASH
