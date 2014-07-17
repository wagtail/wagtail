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

    def crop(self, image, crop_box):
        new_image = image.clone()
        new_image.crop(
            left=crop_box[0], top=crop_box[1], right=crop_box[2], bottom=crop_box[3]
        )
        return new_image
