from __future__ import absolute_import, unicode_literals

import PIL.Image
from django.core.files.images import ImageFile
from django.utils.six import BytesIO

from wagtail.wagtailimages.models import get_image_model

Image = get_image_model()


def get_test_image_file(filename='test.png', colour='white', size=(640, 480)):
    f = BytesIO()
    image = PIL.Image.new('RGB', size, colour)
    image.save(f, 'PNG')
    return ImageFile(f, name=filename)
