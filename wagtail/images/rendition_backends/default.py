from .base import BaseRenditionBackend
from .model import RenditionModelBackendMixin
from .willow import WillowRenditionBackendMixin


class DefaultRenditionBackend(
    WillowRenditionBackendMixin, RenditionModelBackendMixin, BaseRenditionBackend
):
    """
    Wagtail's default rendition backend, which uses a Django model to store and
    retrieve generated renditions, and Willow to generate new image files from
    the original (depending on requirements).
    """

    pass
