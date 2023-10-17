from typing import TYPE_CHECKING, Type, Iterator
from django.conf import settings
from django.utils.module_loading import import_string

from .base import BaseRendition, BaseRenditionBackend  # noqa
from .default import DefaultRenditionBackend  # noqa
from .model import RenditionModelBackendMixin  # noqa
from .willow import WillowRenditionBackendMixin  # noqa

if TYPE_CHECKING:
    from wagtail.images.models import AbstractImage


# Global list of initialised rendition backends, populated by
# ``get_rendition_backends_for_image()`` as and when they are needed.
RENDITION_BACKENDS = []


def get_rendition_backend_classes() -> Iterator[Type]:
    """
    Returns an iteratable of rendition backend classes, whose import paths
    are present in the ``WAGTAILIMAGES_RENDITION_BACKENDS`` setting, in the
    order they are specified.

    If the setting is not present (or has a 'falsey' value), Wagtail's
    ``DefaultRenditionBackend`` class will be the first and only class to
    be returned.
    """
    classnames = getattr(settings, "WAGTAILIMAGES_RENDITION_BACKENDS", None)
    if not classnames:
        yield DefaultRenditionBackend
    else:
        for classname in classnames:
            yield import_string(classname)


def get_rendition_backends_for_image(
    image: "AbstractImage",
) -> list[BaseRenditionBackend]:
    """
    Returns a list of rendition backend instances that meet the
    following criteria, in the order specified in ``WAGTAILIMAGES_RENDITION_BACKENDS``:

    *   The ``is_enabled()`` class method returns ``True``
    *   The ``is supported_for_image()`` class method returns ``True`` for the
        supplied ``image``.

    Once initialised, backend instances are added to the ``RENDITION_BACKENDS``
    global, and reused for the lifetime of the running process.
    """
    applicable_backends = []
    for klass in get_rendition_backend_classes():
        if klass.is_enabled() and klass.is_supported_for_image(image):
            # Reuse an existing instance if available
            found = False
            for backend in RENDITION_BACKENDS:
                if type(backend) == klass:
                    applicable_backends.append(backend)
                    found = True
                    break
            # Otherwise, create a new instance
            if not found:
                backend = klass()
                RENDITION_BACKENDS.append(backend)
                applicable_backends.append(backend)

    return applicable_backends
