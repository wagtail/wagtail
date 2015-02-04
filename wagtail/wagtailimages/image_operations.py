from __future__ import division

import inspect

from wagtail.wagtailimages.exceptions import InvalidFilterSpecError


class Operation(object):
    def __init__(self, method, *args):
        self.method = method
        self.args = args

        # Check arguments
        try:
            inspect.getcallargs(self.construct, *args)
        except TypeError as e:
            raise InvalidFilterSpecError(e)

        # Call construct
        try:
            self.construct(*args)
        except ValueError as e:
            raise InvalidFilterSpecError(e)

    def construct(self, *args):
        raise NotImplementedError

    def run(self, willow, image):
        raise NotImplementedError


class DoNothingOperation(Operation):
    def construct(self):
        pass

    def run(self, willow, image):
        pass


class FillOperation(Operation):
    def construct(self, size, *extra):
        # Get width and height
        width_str, height_str = size.split('x')
        self.width = int(width_str)
        self.height = int(height_str)

        # Crop closeness
        self.crop_closeness = 0

        for extra_part in extra:
            if extra_part.startswith('c'):
                self.crop_closeness = int(extra_part[1:])
            else:
                raise ValueError("Unrecognised filter spec part: %s" % extra_part)

        # Divide it by 100 (as it's a percentage)
        self.crop_closeness /= 100

        # Clamp it
        if self.crop_closeness > 1:
            self.crop_closeness = 1

    def run(self, willow, image):
        image_width, image_height = willow.get_size()
        focal_point = image.get_focal_point()

        # Get crop aspect ratio
        crop_aspect_ratio = self.width / self.height

        # Get crop max
        crop_max_scale = min(image_width, image_height * crop_aspect_ratio)
        crop_max_width = crop_max_scale
        crop_max_height = crop_max_scale / crop_aspect_ratio

        # Initialise crop width and height to max
        crop_width = crop_max_width
        crop_height = crop_max_height

        # Use crop closeness to zoom in
        if focal_point is not None:
            # Get crop min
            crop_min_scale = max(focal_point.width, focal_point.height * crop_aspect_ratio)
            crop_min_width = crop_min_scale
            crop_min_height = crop_min_scale / crop_aspect_ratio

            # Sometimes, the focal point may be bigger than the image...
            if not crop_min_scale >= crop_max_scale:
                # Calculate max crop closeness to prevent upscaling
                max_crop_closeness = max(
                    1 - (self.width - crop_min_width) / (crop_max_width - crop_min_width),
                    1 - (self.height - crop_min_height) / (crop_max_height - crop_min_height)
                )

                # Apply max crop closeness
                crop_closeness = min(self.crop_closeness, max_crop_closeness)

                if 1 >= crop_closeness >= 0:
                    # Get crop width and height
                    crop_width = crop_max_width + (crop_min_width - crop_max_width) * crop_closeness
                    crop_height = crop_max_height + (crop_min_height - crop_max_height) * crop_closeness

        # Find focal point UV
        if focal_point is not None:
            fp_x, fp_y = focal_point.centroid
        else:
            # Fall back to positioning in the centre
            fp_x = image_width / 2
            fp_y = image_height / 2

        fp_u = fp_x / image_width
        fp_v = fp_y / image_height

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
            if left > focal_point.left:
                right -= left - focal_point.left
                left = focal_point.left

            if top > focal_point.top:
                bottom -= top - focal_point.top
                top = focal_point.top

            if right < focal_point.right:
                left += focal_point.right - right
                right = focal_point.right

            if bottom < focal_point.bottom:
                top += focal_point.bottom - bottom
                bottom = focal_point.bottom

        # Don't allow the crop box to go over the image boundary
        if left < 0:
            right -= left
            left = 0

        if top < 0:
            bottom -= top
            top = 0

        if right > image_width:
            left -= right - image_width
            right = image_width

        if bottom > image_height:
            top -= bottom - image_height
            bottom = image_height

        # Crop!
        willow.crop(int(left), int(top), int(right), int(bottom))

        # Resize the final image
        aftercrop_width, aftercrop_height = willow.get_size()
        horz_scale = self.width / aftercrop_width
        vert_scale = self.height / aftercrop_height

        if aftercrop_width <= self.width or aftercrop_height <= self.height:
            return

        if horz_scale > vert_scale:
            width = self.width
            height = int(aftercrop_height * horz_scale)
        else:
            width = int(aftercrop_width * vert_scale)
            height = self.height

        willow.resize(width, height)

    def get_vary(self, image):
        focal_point = image.get_focal_point()

        if focal_point is not None:
            focal_point_key = "%(x)d-%(y)d-%(width)dx%(height)d" % {
                'x': int(focal_point.centroid_x),
                'y': int(focal_point.centroid_y),
                'width': int(focal_point.width),
                'height': int(focal_point.height),
            }
        else:
            focal_point_key = ''

        return [focal_point_key]


class MinMaxOperation(Operation):
    def construct(self, size):
        # Get width and height
        width_str, height_str = size.split('x')
        self.width = int(width_str)
        self.height = int(height_str)

    def run(self, willow, image):
        image_width, image_height = willow.get_size()

        horz_scale = self.width / image_width
        vert_scale = self.height / image_height

        if self.method == 'min':
            if image_width <= self.width or image_height <= self.height:
                return

            if horz_scale > vert_scale:
                width = self.width
                height = int(image_height * horz_scale)
            else:
                width = int(image_width * vert_scale)
                height = self.height

        elif self.method == 'max':
            if image_width <= self.width and image_height <= self.height:
                return

            if horz_scale < vert_scale:
                width = self.width
                height = int(image_height * horz_scale)
            else:
                width = int(image_width * vert_scale)
                height = self.height

        else:
            # Unknown method
            return

        willow.resize(width, height)


class WidthHeightOperation(Operation):
    def construct(self, size):
        self.size = int(size)

    def run(self, willow, image):
        image_width, image_height = willow.get_size()

        if self.method == 'width':
            if image_width <= self.size:
                return

            scale = self.size / image_width

            width = self.size
            height = int(image_height * scale)

        elif self.method == 'height':
            if image_height <= self.size:
                return

            scale = self.size / image_height

            width = int(image_width * scale)
            height = self.size

        else:
            # Unknown method
            return

        willow.resize(width, height)
