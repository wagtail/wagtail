from wagtail.wagtailimages.utils.focal_point import combine_focal_points


class CropBox(object):
    def __init__(self, left, top, right, bottom):
        self.left = int(left)
        self.top = int(top)
        self.right = int(right)
        self.bottom = int(bottom)

    def __getitem__(self, key):
        return (self.left, self.top, self.right, self.bottom)[key]

    @property
    def width(self):
        return self.right - self.left

    @property
    def height(self):
        return self.bottom - self.top

    @property
    def size(self):
        return self.width, self.height


def crop_to_centre(image_size, crop_size):
    (original_width, original_height) = image_size
    (crop_width, crop_height) = crop_size

    # final dimensions should not exceed original dimensions
    final_width = min(original_width, crop_width)
    final_height = min(original_height, crop_height)

    left = (original_width - final_width) / 2
    top = (original_height - final_height) / 2

    return CropBox(left, top, left + final_width, top + final_height)


def crop_to_point(image_size, crop_size, focal_point):
    (original_width, original_height) = image_size
    (crop_width, crop_height) = crop_size

    # Make sure final dimensions do not exceed original dimensions
    final_width = min(original_width, crop_width)
    final_height = min(original_height, crop_height)

    # Get crop box
    left = focal_point.x - final_width / 2
    top = focal_point.y - final_height / 2
    right = focal_point.x + final_width / 2
    bottom = focal_point.y + final_height / 2

    # Don't allow the crop box to go over the image boundary
    if left < 0:
        right -= left
        left = 0

    if top < 0:
        bottom -= top
        top = 0

    if right > original_width:
        left -= right - original_width
        right = original_width

    if bottom > original_height:
        top -= bottom - original_height
        bottom = original_height

    return CropBox(left, top, right, bottom)


def crop_to_points(image_size, crop_size, focal_points):
    focal_point = combine_focal_points(focal_points)
    return crop_to_point(image_size, crop_size, focal_point)
