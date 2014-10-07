from __future__ import absolute_import

from wand.image import Image
from wand.api import library

from wagtail.wagtailimages.backends.base import BaseImageBackend


class WandBackend(BaseImageBackend):
    def __init__(self, params):
        super(WandBackend, self).__init__(params)

    def open_image(self, input_file):
        image = Image(file=input_file)
        image.wand = library.MagickCoalesceImages(image.wand)
        return image

    def save_image(self, image, output, format):
        image.format = format
        image.compression_quality = self.quality
        image.save(file=output)

    def resize(self, image, size):
        new_image = image.clone()
        new_image.resize(size[0], size[1])
        return new_image

    def crop(self, image, rect):
        new_image = image.clone()
        new_image.crop(
            left=rect[0], top=rect[1], right=rect[2], bottom=rect[3]
        )
        return new_image

    def image_data_as_rgb(self, image):
        # Only return image data if this image is not animated
        if image.animation:
            return

        return 'RGB', image.make_blob('RGB')

