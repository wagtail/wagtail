from django.db import models
from django.conf import settings
from base import BaseImageBackend

from wand.image import Image

class WandBackend(BaseImageBackend):
    def __init__(self, params):
        super(WandBackend, self).__init__(params)
        
    def open_image(self, input_file):
        image = Image(file=input_file)
        return image
        
    def save_image(self, image, output, format):
        image.format = format
        image.save(file=output)
        
    def resize(self, image, size):
        image.resize(size[0], size[1])
        return image
        

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
        return image.crop(
            (left, top, left + final_width, top + final_height)
        )