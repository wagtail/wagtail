from django.utils.html import escape

from wagtail.utils.apps import get_app_submodules
from wagtail.wagtailimages.models import SourceImageIOError


class Format(object):
    def __init__(self, name, label, classnames, filter_spec):
        self.name = name
        self.label = label
        self.classnames = classnames
        self.filter_spec = filter_spec

    def editor_attributes(self, image, alt_text):
        """
        Return string of additional attributes to go on the HTML element
        when outputting this image within a rich text editor field
        """
        return 'data-embedtype="image" data-id="%d" data-format="%s" data-alt="%s" ' % (
            image.id, self.name, alt_text
        )

    def image_to_editor_html(self, image, alt_text):
        return self.image_to_html(
            image, alt_text, self.editor_attributes(image, alt_text)
        )

    def image_to_html(self, image, alt_text, extra_attributes=''):
        try:
            rendition = image.get_rendition(self.filter_spec)
        except SourceImageIOError:
            # Image file is (probably) missing from /media/original_images - generate a dummy
            # rendition so that we just output a broken image, rather than crashing out completely
            # during rendering
            Rendition = image.renditions.model  # pick up any custom Image / Rendition classes that may be in use
            rendition = Rendition(image=image, width=0, height=0)
            rendition.file.name = 'not-found'

        if self.classnames:
            class_attr = 'class="%s" ' % escape(self.classnames)
        else:
            class_attr = ''

        return '<img %s%ssrc="%s" width="%d" height="%d" alt="%s">' % (
            extra_attributes, class_attr,
            escape(rendition.url), rendition.width, rendition.height, alt_text
        )


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
        list(get_app_submodules('image_formats'))
        _searched_for_image_formats = True


# Define default image formats
register_image_format(Format('fullwidth', 'Full width', 'richtext-image full-width', 'width-800'))
register_image_format(Format('left', 'Left-aligned', 'richtext-image left', 'width-500'))
register_image_format(Format('right', 'Right-aligned', 'richtext-image right', 'width-500'))
