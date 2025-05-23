from django import template
from jinja2.ext import Extension

from .models import Filter, Picture, ResponsiveImage
from .shortcuts import get_rendition_or_not_found, get_renditions_or_not_found
from .templatetags.wagtailimages_tags import image_url


def image(image, filterspec, **attrs):
    if not image:
        return ""

    if not Filter.pipe_spec_pattern.match(filterspec):
        raise template.TemplateSyntaxError(
            "filter specs in 'image' tag may only contain A-Z, a-z, 0-9, dots, hyphens, pipes and underscores. "
            "(given filter: {})".format(filterspec)
        )

    rendition = get_rendition_or_not_found(image, filterspec)

    if attrs:
        return rendition.img_tag(attrs)
    else:
        return rendition


def srcset_image(image, filterspec, **attrs):
    if not image:
        return ""

    if not Filter.pipe_expanding_spec_pattern.match(filterspec):
        raise template.TemplateSyntaxError(
            "filter specs in 'srcset_image' tag may only contain A-Z, a-z, 0-9, dots, hyphens, curly braces, commas, pipes and underscores. "
            "(given filter: {})".format(filterspec)
        )

    specs = Filter.expand_spec(filterspec)
    renditions = get_renditions_or_not_found(image, specs)

    return ResponsiveImage(renditions, attrs)


def picture(image, filterspec, **attrs):
    if not image:
        return ""

    if not Filter.pipe_expanding_spec_pattern.match(filterspec):
        raise template.TemplateSyntaxError(
            "filter specs in 'picture' tag may only contain A-Z, a-z, 0-9, dots, hyphens, curly braces, commas, pipes and underscores. "
            "(given filter: {})".format(filterspec)
        )

    specs = Filter.expand_spec(filterspec)
    renditions = get_renditions_or_not_found(image, specs)

    return Picture(renditions, attrs)


class WagtailImagesExtension(Extension):
    def __init__(self, environment):
        super().__init__(environment)

        self.environment.globals.update(
            {
                "image": image,
                "image_url": image_url,
                "srcset_image": srcset_image,
                "picture": picture,
            }
        )


# Nicer import names
images = WagtailImagesExtension
