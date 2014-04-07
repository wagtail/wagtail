from base import BaseImageBackend
import PIL.Image

class PillowBackend(BaseImageBackend):
    def __init__(self, params):
        super(PillowBackend, self).__init__(params)

    def open_image(self, input_file):
        image = PIL.Image.open(input_file)
        return image
        
    def save_image(self, image, output, format):
        if self.quality:
            image.save(output, format, quality=self.quality)
        else:
            image.save(output, format)
    
        
    def resize(self, image, size):
        if image.mode in ['1', 'P']:
            image = image.convert('RGB')
        return image.resize(size, PIL.Image.ANTIALIAS)


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