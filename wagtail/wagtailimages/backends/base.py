from __future__ import division

from django.conf import settings

from wagtail.wagtailimages.rect import Rect


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

        # Get image width and height
        (im_width, im_height) = image.size

        # Get filter width and height
        fl_width = size[0]
        fl_height = size[1]

        # Get crop aspect ratio
        crop_aspect_ratio = fl_width / fl_height

        # Get crop max
        crop_max_scale = min(im_width, im_height * crop_aspect_ratio)
        crop_max_width = crop_max_scale
        crop_max_height = crop_max_scale / crop_aspect_ratio

        # Initialise crop width and height to max
        crop_width = crop_max_width
        crop_height = crop_max_height

        # Use crop closeness to zoom in
        if focal_point is not None:
            fp_width = focal_point.width
            fp_height = focal_point.height

            # Get crop min
            crop_min_scale = max(fp_width, fp_height * crop_aspect_ratio)
            crop_min_width = crop_min_scale
            crop_min_height = crop_min_scale / crop_aspect_ratio

            # Sometimes, the focal point may be bigger than the image...
            if not crop_min_scale >= crop_max_scale:
                # Calculate max crop closeness to prevent upscaling
                max_crop_closeness = max(
                    1 - (fl_width - crop_min_width) / (crop_max_width - crop_min_width),
                    1 - (fl_height - crop_min_height) / (crop_max_height - crop_min_height)
                )

                # Apply max crop closeness
                crop_closeness = min(crop_closeness, max_crop_closeness)

                if 1 >= crop_closeness >= 0:
                    # Get crop width and height
                    crop_width = crop_max_width + (crop_min_width - crop_max_width) * crop_closeness
                    crop_height = crop_max_height + (crop_min_height - crop_max_height) * crop_closeness

        # Find focal point UV
        if focal_point is not None:
            fp_x, fp_y = focal_point.centroid
        else:
            # Fall back to positioning in the centre
            fp_x = im_width / 2
            fp_y = im_height / 2

        fp_u = fp_x / im_width
        fp_v = fp_y / im_height

        # Position crop box based on focal point UV
        crop_x = fp_x - (fp_u - 0.5) * crop_width
        crop_y = fp_y - (fp_v - 0.5) * crop_height

        # Convert crop box into rect
        left = crop_x - crop_width / 2
        top = crop_y - crop_height / 2
        right = crop_x + crop_width / 2
        bottom = crop_y + crop_height / 2

        # Make sure the entire focal point is in the crop box
        if focal_point is not None:
            focal_point_left = focal_point.left
            focal_point_top = focal_point.top
            focal_point_right = focal_point.right
            focal_point_bottom = focal_point.bottom

            if left > focal_point_left:
                right -= left - focal_point_left
                left = focal_point_left

            if top > focal_point_top:
                bottom -= top - focal_point_top
                top = focal_point_top

            if right < focal_point_right:
                left += focal_point_right - right
                right = focal_point_right

            if bottom < focal_point_bottom:
                top += focal_point_bottom - bottom
                bottom = focal_point_bottom

        # Don't allow the crop box to go over the image boundary
        if left < 0:
            right -= left
            left = 0

        if top < 0:
            bottom -= top
            top = 0

        if right > im_width:
            left -= right - im_width
            right = im_width

        if bottom > im_height:
            top -= bottom - im_height
            bottom = im_height

        # Crop!
        return self.resize_to_min(self.crop(image, Rect(left, top, right, bottom)), size)

    def no_operation(self, image, param, focal_point=None):
        """Return the image unchanged"""
        return image
