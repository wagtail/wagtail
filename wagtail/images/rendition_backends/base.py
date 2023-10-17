from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import TYPE_CHECKING

from django.apps import apps
from django.conf import settings
from django.forms.utils import flatatt
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe

from wagtail.images.filters import Filter

if TYPE_CHECKING:
    from wagtail.images.models import AbstractImage


class BaseRendition(ABC):
    """
    An abstract base class for rendition types, covering the basic API
    requirements. At the very least, a rendition must be capable of rendering
    iteslf as an <img> tag with the appropriate attribute values.
    """

    filter_spec: str = ""

    @cached_property
    def filter(self):
        return Filter(self.filter_spec)

    @property
    @abstractmethod
    def url(self) -> str:
        return NotImplemented

    @property
    def full_url(self):
        url = self.url
        if hasattr(settings, "WAGTAILADMIN_BASE_URL") and url.startswith("/"):
            return settings.WAGTAILADMIN_BASE_URL + url
        return url

    @property
    @abstractmethod
    def height(self) -> int:
        return NotImplemented

    @property
    @abstractmethod
    def width(self) -> int:
        return NotImplemented

    @property
    @abstractmethod
    def alt(self) -> str:
        return NotImplemented

    def get_img_attrs(self):
        """
        A dict of the src, width, height, and alt attributes for an <img> tag.
        """
        return OrderedDict(
            [
                ("src", self.url),
                ("width", self.width),
                ("height", self.height),
                ("alt", self.alt),
            ]
        )

    @property
    def attrs(self):
        """
        The src, width, height, and alt attributes for an <img> tag, as a HTML
        string
        """
        return flatatt(self.get_img_attrs())

    def img_tag(self, extra_attributes={}):
        attrs = {}
        attrs.update(self.get_img_attrs())
        attrs.update(apps.get_app_config("wagtailimages").default_attrs)
        attrs.update(extra_attributes)
        return mark_safe(f"<img{flatatt(attrs)}>")

    def __html__(self):
        return self.img_tag()


class BaseRenditionBackend(ABC):
    """
    An abstract base class for 'rendition backends', that are responsible
    for transforming image / filter combinations into `BaseRendition` instances
    that can be rendered in templates and elsewhere.
    """

    @classmethod
    def is_enabled(cls):
        """
        All rendition backends report as 'enabled' by default. Subclasses
        might want to override this to disable themselves in certain
        circumstances. For example, if required configuration values have
        not been set for a specific environment.
        """
        return True

    @classmethod
    def is_supported_for_image(cls, image: "AbstractImage") -> bool:
        """
        When generating renditions for a specifc image, all rendition backends
        report as being capable of providing renditions for that image by
        default. Subclasses might want to override this to skip certain image
        backends for specific image (for example, if the original image is in
        a format not supported by the backend).
        """
        return True

    @abstractmethod
    def get_rendition(
        self, image: "AbstractImage", filter: Filter | str
    ) -> BaseRendition:
        """
        Return a rendition object for the provided image matching the provided
        filter/spec.
        """
        return NotImplemented

    def get_renditions(
        self, image: "AbstractImage", *filter_specs: str
    ) -> dict[str, BaseRendition]:
        """
        Returns a dictionary mapping the required filter specs to rendition
        objects for the provided image.
        """
        return {spec: self.get_rendition(image, spec) for spec in filter_specs}
