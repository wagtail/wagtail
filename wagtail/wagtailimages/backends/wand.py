from __future__ import absolute_import
from __future__ import division

from .base import BaseImageBackend
from wand.image import Image
from wand.api import library


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

    def liquid_resize(self, image, size):
        new_aspect_ratio = size[0] / size[1]

        (original_width, original_height) = image.size
        original_aspect_ratio = original_width / original_height

        if original_aspect_ratio < new_aspect_ratio:
            new_width = original_width
            new_height = original_width / new_aspect_ratio
        else:
            new_width = original_height * new_aspect_ratio
            new_height = original_height

        new_image = image.clone()
        new_image.liquid_rescale(int(new_width), int(new_height))
        new_image.resize(size[0], size[1])
        return new_image

    def crop_to_centre(self, image, size):
        (original_width, original_height) = image.size
        (target_width, target_height) = size

        # final dimensions should not exceed original dimensions
        final_width = min(original_width, target_width)
        final_height = min(original_height, target_height)

        if final_width == original_width and final_height == original_height:
            return image

        left = (original_width - final_width) / 2
        top = (original_height - final_height) / 2

        new_image = image.clone()
        new_image.crop(
            left=left, top=top, right=left + final_width, bottom=top + final_height
        )
        return new_image
