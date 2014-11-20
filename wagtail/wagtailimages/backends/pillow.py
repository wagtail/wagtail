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

    def _to_rgb(self, image):
        if image.mode not in ['RGB', 'RGBA']:
            if 'transparency' in image.info and isinstance(image.info['transparency'], bytes):
                image = image.convert('RGBA')
            else:
                image = image.convert('RGB')
        return image

    def resize(self, image, size):
        return self._to_rgb(image).resize(size, PIL.Image.ANTIALIAS)

    def crop(self, image, rect):
        return image.crop(rect)

    def image_data_as_rgb(self, image):
        image = self._to_rgb(image)
        return image.mode, image.tostring()
