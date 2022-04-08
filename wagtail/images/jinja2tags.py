import re

from django import template
from jinja2.ext import Extension

from .shortcuts import get_rendition_or_not_found
from .templatetags.wagtailimages_tags import image_url

allowed_filter_pattern = re.compile(r"^[A-Za-z0-9_\-\.\|]+$")


def image(image, filterspec, **attrs):
    if not image:
        return ""

    if not allowed_filter_pattern.match(filterspec):
        raise template.TemplateSyntaxError(
            "filter specs in 'image' tag may only contain A-Z, a-z, 0-9, dots, hyphens, pipes and underscores. "
            "(given filter: {})".format(filterspec)
        )

    rendition = get_rendition_or_not_found(image, filterspec)

    if attrs:
        return rendition.img_tag(attrs)
    else:
        return rendition


class WagtailImagesExtension(Extension):
    def __init__(self, environment):
        super().__init__(environment)

        self.environment.globals.update(
            {
                "image": image,
                "image_url": image_url,
            }
        )


# Nicer import names
images = WagtailImagesExtension
