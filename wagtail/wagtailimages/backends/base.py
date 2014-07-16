from django.conf import settings


class BaseImageBackend(object):
    def __init__(self, params):
        self.quality = getattr(settings, 'IMAGE_COMPRESSION_QUALITY', 85)

    def open_image(self, input_file):
        """
        Open an image and return the backend specific image object to pass
        to other methods. The object return has to have a size  attribute
        which is a tuple with the width and height of the image and a format
        attribute with the format of the image.
        """
        raise NotImplementedError('subclasses of BaseImageBackend must provide an open_image() method')

    def save_image(self, image, output):
        """
        Save the image to the output
        """
        raise NotImplementedError('subclasses of BaseImageBackend must provide a save_image() method')

    def resize(self, image, size):
        """
        resize image to the requested size, using highest quality settings
        (antialiasing enabled, converting to true colour if required)
        """
        raise NotImplementedError('subclasses of BaseImageBackend must provide an resize() method')

    def crop_to_centre(self, image, size):
        raise NotImplementedError('subclasses of BaseImageBackend must provide a crop_to_centre() method')

    def resize_to_max(self, image, size):
        """
        Resize image down to fit within the given dimensions, preserving aspect ratio.
        Will leave image unchanged if it's already within those dimensions.
        """
        (original_width, original_height) = image.size
        (target_width, target_height) = size

        if original_width <= target_width and original_height <= target_height:
            return image

        # scale factor if we were to downsize the image to fit the target width
        horz_scale = float(target_width) / original_width
        # scale factor if we were to downsize the image to fit the target height
        vert_scale = float(target_height) / original_height

        # choose whichever of these gives a smaller image
        if horz_scale < vert_scale:
            final_size = (target_width, int(original_height * horz_scale))
        else:
            final_size = (int(original_width * vert_scale), target_height)

        return self.resize(image, final_size)

    def resize_to_min(self, image, size):
        """
        Resize image down to cover the given dimensions, preserving aspect ratio.
        Will leave image unchanged if width or height is already within those limits.
        """
        (original_width, original_height) = image.size
        (target_width, target_height) = size

        if original_width <= target_width or original_height <= target_height:
            return image

        # scale factor if we were to downsize the image to fit the target width
        horz_scale = float(target_width) / original_width
        # scale factor if we were to downsize the image to fit the target height
        vert_scale = float(target_height) / original_height

        # choose whichever of these gives a larger image
        if horz_scale > vert_scale:
            final_size = (target_width, int(original_height * horz_scale))
        else:
            final_size = (int(original_width * vert_scale), target_height)

        return self.resize(image, final_size)

    def resize_to_width(self, image, target_width):
        """
        Resize image down to the given width, preserving aspect ratio.
        Will leave image unchanged if it's already within that width.
        """
        (original_width, original_height) = image.size

        if original_width <= target_width:
            return image

        scale = float(target_width) / original_width

        final_size = (target_width, int(original_height * scale))

        return self.resize(image, final_size)

    def resize_to_height(self, image, target_height):
        """
        Resize image down to the given height, preserving aspect ratio.
        Will leave image unchanged if it's already within that height.
        """
        (original_width, original_height) = image.size

        if original_height <= target_height:
            return image

        scale = float(target_height) / original_height

        final_size = (int(original_width * scale), target_height)

        return self.resize(image, final_size)

    def resize_to_fill(self, image, size):
        """
        Resize down and crop image to fill the given dimensions. Most suitable for thumbnails.
        (The final image will match the requested size, unless one or the other dimension is
        already smaller than the target size)
        """
        resized_image = self.resize_to_min(image, size)
        return self.crop_to_centre(resized_image, size)


    def no_operation(self, image, param):
        """Return the image unchanged"""
        return image
