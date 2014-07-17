from __future__ import absolute_import

import PIL.Image

from wagtail.wagtailimages.backends.base import BaseImageBackend


class PillowBackend(BaseImageBackend):
    def __init__(self, params):
        super(PillowBackend, self).__init__(params)

    def open_image(self, input_file):
        image = PIL.Image.open(input_file)
        return image

    def save_image(self, image, output, format):
        image.save(output, format, quality=self.quality)

    def resize(self, image, size):
        if image.mode in ['1', 'P']:
            image = image.convert('RGB')
        return image.resize(size, PIL.Image.ANTIALIAS)

    def crop(self, image, crop_box):
        return image.crop(crop_box)


