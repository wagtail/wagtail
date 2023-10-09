from warnings import warn

from django.utils.html import escape
from django.utils.translation import gettext_lazy as _

from wagtail.utils.apps import get_app_submodules
from wagtail.utils.deprecation import RemovedInWagtail60Warning

from .shortcuts import get_rendition_or_not_found


class Format:
    def __init__(self, name, label, classname, filter_spec):
        self.name = name
        self.label = label
        self.classname = classname
        self.filter_spec = filter_spec

    def __str__(self):
        return (
            f'"{self.name}", "{self.label}", "{self.classname}", "{self.filter_spec}"'
        )

    def __repr__(self):
        return f"Format({self})"

    @property
    def classnames(self):
        warn(
            "The class property `classnames` is deprecated - use `classname` instead.",
            category=RemovedInWagtail60Warning,
        )
        return self.classname

    def editor_attributes(self, image, alt_text):
        """
        Return additional attributes to go on the HTML element
        when outputting this image within a rich text editor field
        """
        return {
            "data-embedtype": "image",
            "data-id": image.id,
            "data-format": self.name,
            "data-alt": escape(alt_text),
        }

    def image_to_editor_html(self, image, alt_text):
        return self.image_to_html(
            image, alt_text, self.editor_attributes(image, alt_text)
        )

    def image_to_html(self, image, alt_text, extra_attributes=None):
        if extra_attributes is None:
            extra_attributes = {}
        rendition = get_rendition_or_not_found(image, self.filter_spec)

        extra_attributes["alt"] = escape(alt_text)
        if self.classname:
            extra_attributes["class"] = "%s" % escape(self.classname)

        return rendition.img_tag(extra_attributes)


FORMATS = []
FORMATS_BY_NAME = {}


def register_image_format(format):
    if format.name in FORMATS_BY_NAME:
        raise KeyError("Image format '%s' is already registered" % format.name)
    FORMATS_BY_NAME[format.name] = format
    FORMATS.append(format)


def unregister_image_format(format_name):
    global FORMATS
    # handle being passed a format object rather than a format name string
    try:
        format_name = format_name.name
    except AttributeError:
        pass

    try:
        del FORMATS_BY_NAME[format_name]
        FORMATS = [fmt for fmt in FORMATS if fmt.name != format_name]
    except KeyError:
        raise KeyError("Image format '%s' is not registered" % format_name)


def get_image_formats():
    search_for_image_formats()
    return FORMATS


def get_image_format(name):
    search_for_image_formats()
    return FORMATS_BY_NAME[name]


_searched_for_image_formats = False


def search_for_image_formats():
    global _searched_for_image_formats
    if not _searched_for_image_formats:
        list(get_app_submodules("image_formats"))
        _searched_for_image_formats = True


# Define default image formats
register_image_format(
    Format("fullwidth", _("Full width"), "richtext-image full-width", "width-800")
)
register_image_format(
    Format("left", _("Left-aligned"), "richtext-image left", "width-500")
)
register_image_format(
    Format("right", _("Right-aligned"), "richtext-image right", "width-500")
)
