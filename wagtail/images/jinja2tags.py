from jinja2.ext import Extension

from .shortcuts import get_rendition_or_not_found
from .templatetags.wagtailimages_tags import image_url


def image(image, filterspec, **attrs):
    if not image:
        return ''

    rendition = get_rendition_or_not_found(image, filterspec)

    if attrs:
        return rendition.img_tag(attrs)
    else:
        return rendition


class WagtailImagesExtension(Extension):
    def __init__(self, environment):
        super().__init__(environment)

        self.environment.globals.update({
            'image': image,
            'image_url': image_url,
        })


# Nicer import names
images = WagtailImagesExtension
