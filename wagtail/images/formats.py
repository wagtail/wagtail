import warnings

from django.utils.html import escape
from django.utils.translation import gettext_lazy as _

from wagtail.utils.apps import get_app_submodules

from .shortcuts import get_rendition_or_not_found


class Format:
    def __init__(self, name, label, classnames, filter_spec):
        self.name = name
        self.label = label
        self.classnames = classnames
        self.filter_spec = filter_spec

    def __str__(self):
        return (
            f'"{self.name}", "{self.label}", "{self.classnames}", "{self.filter_spec}"'
        )

    def __repr__(self):
        return f"Format({self})"

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
        if self.classnames:
            extra_attributes["class"] = "%s" % escape(self.classnames)

        return rendition.img_tag(extra_attributes)


FORMATS = []
FORMATS_BY_NAME = {}
FALLBACK_FORMAT = None


def register_image_format(format, is_fallback=False):
    if format.name in FORMATS_BY_NAME:
        raise KeyError("Image format '%s' is already registered" % format.name)
    FORMATS_BY_NAME[format.name] = format
    FORMATS.append(format)

    if is_fallback:
        global FALLBACK_FORMAT
        FALLBACK_FORMAT = format.name


def unregister_image_format(format_name):
    global FORMATS, FALLBACK_FORMAT
    # handle being passed a format object rather than a format name string
    try:
        format_name = format_name.name
    except AttributeError:
        pass

    try:
        del FORMATS_BY_NAME[format_name]
        FORMATS = [fmt for fmt in FORMATS if fmt.name != format_name]

        # Check if the removed format was the fallback format
        if FALLBACK_FORMAT == format_name:
            FALLBACK_FORMAT = None

    except KeyError:
        raise KeyError("Image format '%s' is not registered" % format_name)


def get_image_formats():
    search_for_image_formats()
    return FORMATS


def get_image_format(name):
    search_for_image_formats()
    if name in FORMATS_BY_NAME:
        return FORMATS_BY_NAME[name]
    elif FALLBACK_FORMAT:
        warnings.warn(
            f"Using fallback image format '{FALLBACK_FORMAT}' for '{name}'", UserWarning
        )
        return FORMATS_BY_NAME[FALLBACK_FORMAT]
    else:
        raise KeyError("Image format '%s' not found and no fallback format set" % name)


_searched_for_image_formats = False


def search_for_image_formats():
    global _searched_for_image_formats
    if not _searched_for_image_formats:
        list(get_app_submodules("image_formats"))
        _searched_for_image_formats = True


# Define default image formats
register_image_format(
    Format("fullwidth", _("Full width"), "richtext-image full-width", "width-800"),
    is_fallback=True,
)
register_image_format(
    Format("left", _("Left-aligned"), "richtext-image left", "width-500")
)
register_image_format(
    Format("right", _("Right-aligned"), "richtext-image right", "width-500")
)
