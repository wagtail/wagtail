from __future__ import division

from django.conf import settings

from wagtail.wagtailimages.utils import crop
from wagtail.wagtailimages.utils.focal_point import FocalPoint


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

    def image_data_as_rgb(self, image):
        raise NotImplementedError('subclasses of BaseImageBackend must provide an image_data_as_rgb() method')

    def crop(self, image, crop_box):
        raise NotImplementedError('subclasses of BaseImageBackend must provide a crop() method')

    def crop_to_centre(self, image, size):
        crop_box = crop.crop_to_centre(image.size, size)
        if crop_box.size != image.size:
            return self.crop(image, crop_box)
        else:
            return image

    def crop_to_point(self, image, size, focal_point):
        crop_box = crop.crop_to_point(image.size, size, focal_point)

        # Don't crop if we don't need to
        if crop_box.size != image.size:
            image = self.crop(image, crop_box)

        # If the focal points are too large, the cropping system may not
        # crop it fully, resize the image if this has happened:
        if crop_box.size != size:
            image = self.resize_to_fill(image, size)

        return image

    def resize_to_max(self, image, size, focal_point=None):
        """
        Resize image down to fit within the given dimensions, preserving aspect ratio.
        Will leave image unchanged if it's already within those dimensions.
        """
        (original_width, original_height) = image.size
        (target_width, target_height) = size

        if original_width <= target_width and original_height <= target_height:
            return image

        # scale factor if we were to downsize the image to fit the target width
        horz_scale = target_width / original_width
        # scale factor if we were to downsize the image to fit the target height
        vert_scale = target_height / original_height

        # choose whichever of these gives a smaller image
        if horz_scale < vert_scale:
            final_size = (target_width, int(original_height * horz_scale))
        else:
            final_size = (int(original_width * vert_scale), target_height)

        return self.resize(image, final_size)

    def resize_to_min(self, image, size, focal_point=None):
        """
        Resize image down to cover the given dimensions, preserving aspect ratio.
        Will leave image unchanged if width or height is already within those limits.
        """
        (original_width, original_height) = image.size
        (target_width, target_height) = size

        if original_width <= target_width or original_height <= target_height:
            return image

        # scale factor if we were to downsize the image to fit the target width
        horz_scale = target_width / original_width
        # scale factor if we were to downsize the image to fit the target height
        vert_scale = target_height / original_height

        # choose whichever of these gives a larger image
        if horz_scale > vert_scale:
            final_size = (target_width, int(original_height * horz_scale))
        else:
            final_size = (int(original_width * vert_scale), target_height)

        return self.resize(image, final_size)

    def resize_to_width(self, image, target_width, focal_point=None):
        """
        Resize image down to the given width, preserving aspect ratio.
        Will leave image unchanged if it's already within that width.
        """
        (original_width, original_height) = image.size

        if original_width <= target_width:
            return image

        scale = target_width / original_width

        final_size = (target_width, int(original_height * scale))

        return self.resize(image, final_size)

    def resize_to_height(self, image, target_height, focal_point=None):
        """
        Resize image down to the given height, preserving aspect ratio.
        Will leave image unchanged if it's already within that height.
        """
        (original_width, original_height) = image.size

        if original_height <= target_height:
            return image

        scale = target_height / original_height

        final_size = (int(original_width * scale), target_height)

        return self.resize(image, final_size)

    def resize_to_fill(self, image, arg, focal_point=None):
        """
        Resize down and crop image to fill the given dimensions. Most suitable for thumbnails.
        (The final image will match the requested size, unless one or the other dimension is
        already smaller than the target size)
        """
        size = arg[:2]

        # Get crop closeness if it's set
        if len(arg) > 2 and arg[2] is not None:
            crop_closeness = arg[2] / 100

            # Clamp it
            if crop_closeness > 1:
                crop_closeness = 1
        else:
            crop_closeness = 0

        if focal_point is not None and crop_closeness > 0:
            # Get focal point as a rect
            left = focal_point.x - focal_point.width / 2
            top = focal_point.y - focal_point.height / 2
            right = focal_point.x + focal_point.width / 2
            bottom = focal_point.y + focal_point.height / 2

            # Interpolate focal point rect with the images original size by crop closeness
            # When crop_closeness = 0: new FP = image size
            # When crop_closeness = 1: new FP = original FP size
            (original_width, original_height) = image.size
            left = left * crop_closeness
            top = top * crop_closeness
            right = (right - original_width) * crop_closeness + original_width
            bottom = (bottom - original_height) * crop_closeness + original_height

            # Create new focal point
            new_x = (left + right) / 2
            new_y = (top + bottom) / 2
            new_width = right - left
            new_height = bottom - top
            new_focal_point = FocalPoint(new_x, new_y, width=new_width, height=new_height)

            # Crop
            return self.crop_to_point(image, size, new_focal_point)
        else:
            resized_image = self.resize_to_min(image, size)
            return self.crop_to_centre(resized_image, size)

    def no_operation(self, image, param, focal_point=None):
        """Return the image unchanged"""
        return image
