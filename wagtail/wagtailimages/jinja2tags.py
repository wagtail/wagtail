from __future__ import absolute_import

from jinja2.ext import Extension

from .shortcuts import get_rendition_or_not_found


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
        super(WagtailImagesExtension, self).__init__(environment)

        self.environment.globals.update({
            'image': image,
        })


# Nicer import names
images = WagtailImagesExtension
