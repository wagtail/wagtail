# Backend loading
# Based on the Django cache framework and wagtailsearch
# https://github.com/django/django/blob/5d263dee304fdaf95e18d2f0619d6925984a7f02/django/core/cache/__init__.py


from django.utils.module_loading import import_string
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings


class InvalidImageBackendError(ImproperlyConfigured):
    pass


def get_image_backend(backend='default', **kwargs):
    # Get configuration
    default_conf = {
        'default': {
            'BACKEND': 'wagtail.wagtailimages.backends.pillow.PillowBackend',
        },
    }
    WAGTAILIMAGES_BACKENDS = getattr(
        settings, 'WAGTAILIMAGES_BACKENDS', default_conf)

    # Try to find the backend
    try:
        # Try to get the WAGTAILIMAGES_BACKENDS entry for the given backend name first
        conf = WAGTAILIMAGES_BACKENDS[backend]
    except KeyError:
        try:
            # Trying to import the given backend, in case it's a dotted path
            import_string(backend)
        except ImportError as e:
            raise InvalidImageBackendError("Could not find backend '%s': %s" % (
                backend, e))
        params = kwargs
    else:
        # Backend is a conf entry
        params = conf.copy()
        params.update(kwargs)
        backend = params.pop('BACKEND')

    # Try to import the backend
    try:
        backend_cls = import_string(backend)
    except ImportError as e:
        raise InvalidImageBackendError("Could not find backend '%s': %s" % (
            backend, e))

    # Create backend
    return backend_cls(params)
