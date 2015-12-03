from __future__ import absolute_import

from jinja2.ext import Extension

from wagtail.wagtailimages.models import SourceImageIOError


def image(image, filterspec, **attrs):
    if not image:
        return ''

    try:
        rendition = image.get_rendition(filterspec)
    except SourceImageIOError:
        # It's fairly routine for people to pull down remote databases to their
        # local dev versions without retrieving the corresponding image files.
        # In such a case, we would get a SourceImageIOError at the point where we try to
        # create the resized version of a non-existent image. Since this is a
        # bit catastrophic for a missing image, we'll substitute a dummy
        # Rendition object so that we just output a broken link instead.
        Rendition = image.renditions.model  # pick up any custom Image / Rendition classes that may be in use
        rendition = Rendition(image=image, width=0, height=0)
        rendition.file.name = 'not-found'

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
