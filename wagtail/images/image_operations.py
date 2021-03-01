import inspect

from wagtail.images.exceptions import InvalidFilterSpecError
from wagtail.images.rect import Rect, Vector
from wagtail.images.utils import parse_color_string


class Operation:
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


# Transforms


class ImageTransform:
    """
    Tracks transformations that are performed on an image.

    This allows multiple transforms to be processed in a single operation and also
    accumulates the operations into a single scale/offset which can be used for
    features such as transforming the focal point of the image.
    """
    def __init__(self, size):
        self._check_size(size)
        self.size = size
        self.scale = (1.0, 1.0)
        self.offset = (0.0, 0.0)

    def clone(self):
        clone = ImageTransform(self.size)
        clone.scale = self.scale
        clone.offset = self.offset
        return clone

    def resize(self, size):
        """
        Change the image size, stretching the transform to make it fit the new size.
        """
        self._check_size(size)
        clone = self.clone()
        clone.scale = (
            clone.scale[0] * size[0] / self.size[0],
            clone.scale[1] * size[1] / self.size[1]
        )
        clone.size = size
        return clone

    def crop(self, rect):
        """
        Crop the image to the specified rect.
        """
        self._check_size(tuple(rect.size))

        # Transform the image so the top left of the rect is at (0, 0), then set the size
        clone = self.clone()
        clone.offset = (
            clone.offset[0] - rect.left / self.scale[0],
            clone.offset[1] - rect.top / self.scale[1]
        )
        clone.size = tuple(rect.size)
        return clone

    def transform_vector(self, vector):
        """
        Transforms the given vector into the coordinate space of the final image.

        Use this to find out where a point on the source image would end up in the
        final image after cropping/resizing has been performed.

        Returns a new vector.
        """
        return Vector(
            (vector.x + self.offset[0]) * self.scale[0],
            (vector.y + self.offset[1]) * self.scale[1]
        )

    def untransform_vector(self, vector):
        """
        Transforms the given vector back to the coordinate space of the source image.

        This performs the inverse of `transform_vector`. Use this to find where a point
        in the final cropped/resized image originated from in the source image.

        Returns a new vector.
        """
        return Vector(
            vector.x / self.scale[0] - self.offset[0],
            vector.y / self.scale[1] - self.offset[1]
        )

    def get_rect(self):
        """
        Returns a Rect representing the region of the original image to be cropped.
        """
        return Rect(
            -self.offset[0],
            -self.offset[1],
            -self.offset[0] + self.size[0] / self.scale[0],
            -self.offset[1] + self.size[1] / self.scale[1]
        )

    @staticmethod
    def _check_size(size):
        if not isinstance(size, tuple) or len(size) != 2 or int(size[0]) != size[0] or int(size[1]) != size[1]:
            raise TypeError("Image size must be a 2-tuple of integers")

        if size[0] < 1 or size[1] < 1:
            raise ValueError("Image width and height must both be 1 or greater")


class TransformOperation(Operation):
    def run(self, image, transform):
        raise NotImplementedError


class FillOperation(TransformOperation):
    vary_fields = ('focal_point_width', 'focal_point_height', 'focal_point_x', 'focal_point_y')

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

    def run(self, transform, image):
        image_width, image_height = transform.size
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
        rect = Rect.from_point(crop_x, crop_y, crop_width, crop_height)

        # Make sure the entire focal point is in the crop box
        if focal_point is not None:
            rect = rect.move_to_cover(focal_point)

        # Don't allow the crop box to go over the image boundary
        rect = rect.move_to_clamp(Rect(0, 0, image_width, image_height))

        # Crop!
        transform = transform.crop(rect.round())

        # Get scale for resizing
        # The scale should be the same for both the horizontal and
        # vertical axes
        aftercrop_width, aftercrop_height = transform.size
        scale = self.width / aftercrop_width

        # Only resize if the image is too big
        if scale < 1.0:
            # Resize!
            transform = transform.resize((self.width, self.height))

        return transform


class MinMaxOperation(TransformOperation):
    def construct(self, size):
        # Get width and height
        width_str, height_str = size.split('x')
        self.width = int(width_str)
        self.height = int(height_str)

    def run(self, transform, image):
        image_width, image_height = transform.size

        horz_scale = self.width / image_width
        vert_scale = self.height / image_height

        if self.method == 'min':
            if image_width <= self.width or image_height <= self.height:
                return transform

            if horz_scale > vert_scale:
                width = self.width
                height = int(image_height * horz_scale)
            else:
                width = int(image_width * vert_scale)
                height = self.height

        elif self.method == 'max':
            if image_width <= self.width and image_height <= self.height:
                return transform

            if horz_scale < vert_scale:
                width = self.width
                height = int(image_height * horz_scale)
            else:
                width = int(image_width * vert_scale)
                height = self.height

        else:
            # Unknown method
            return transform

        # prevent zero width or height, it causes a ValueError on transform.resize
        width = width if width > 0 else 1
        height = height if height > 0 else 1

        return transform.resize((width, height))


class WidthHeightOperation(TransformOperation):
    def construct(self, size):
        self.size = int(size)

    def run(self, transform, image):
        image_width, image_height = transform.size

        if self.method == 'width':
            if image_width <= self.size:
                return transform

            scale = self.size / image_width

            width = self.size
            height = int(image_height * scale)

        elif self.method == 'height':
            if image_height <= self.size:
                return transform

            scale = self.size / image_height

            width = int(image_width * scale)
            height = self.size

        else:
            # Unknown method
            return transform

        # prevent zero width or height, it causes a ValueError on transform.resize
        width = width if width > 0 else 1
        height = height if height > 0 else 1

        return transform.resize((width, height))


class ScaleOperation(TransformOperation):
    def construct(self, percent):
        self.percent = float(percent)

    def run(self, transform, image):
        image_width, image_height = transform.size

        scale = self.percent / 100
        width = int(image_width * scale)
        height = int(image_height * scale)

        # prevent zero width or height, it causes a ValueError on transform.resize
        width = width if width > 0 else 1
        height = height if height > 0 else 1

        return transform.resize((width, height))


# Filters


class FilterOperation(Operation):
    def run(self, willow, image, env):
        raise NotImplementedError


class DoNothingOperation(FilterOperation):
    def construct(self):
        pass

    def run(self, willow, image, env):
        return willow


class JPEGQualityOperation(FilterOperation):
    def construct(self, quality):
        self.quality = int(quality)

        if self.quality > 100:
            raise ValueError("JPEG quality must not be higher than 100")

    def run(self, willow, image, env):
        env['jpeg-quality'] = self.quality


class WebPQualityOperation(FilterOperation):
    def construct(self, quality):
        self.quality = int(quality)

        if self.quality > 100:
            raise ValueError("WebP quality must not be higher than 100")

    def run(self, willow, image, env):
        env['webp-quality'] = self.quality


class FormatOperation(FilterOperation):
    def construct(self, format, *options):
        self.format = format
        self.options = options

        if self.format not in ['jpeg', 'png', 'gif', 'webp']:
            raise ValueError(
                "Format must be either 'jpeg', 'png', 'gif', or 'webp'")

    def run(self, willow, image, env):
        env['output-format'] = self.format
        env['output-format-options'] = self.options


class BackgroundColorOperation(FilterOperation):
    def construct(self, color_string):
        self.color = parse_color_string(color_string)

    def run(self, willow, image, env):
        return willow.set_background_color_rgb(self.color)
