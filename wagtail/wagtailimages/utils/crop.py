from wagtail.wagtailimages.utils.focal_point import FocalPoint, combine_focal_points


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

    if not focal_point:
        focal_point = FocalPoint(original_width / 2, original_height / 2)

    # Get size of focal point, add 15% extra to give some room around the edge
    focal_point_width = focal_point.width * 1.15
    focal_point_height = focal_point.height * 1.15

    # Make sure that the crop size is no smaller than the focal point
    crop_width = max(crop_width, focal_point_width)
    crop_height = max(crop_height, focal_point_height)

    # Make sure final dimensions do not exceed original dimensions
    final_width = min(original_width, crop_width)
    final_height = min(original_height, crop_height)

    # Get UV for focal point
    focal_point_u = focal_point.x / original_width
    focal_point_v = focal_point.y / original_height

    # Get crop box
    left = focal_point.x - focal_point_u * final_width
    top = focal_point.y - focal_point_v * final_height
    right = focal_point.x - focal_point_u * final_width + final_width
    bottom = focal_point.y - focal_point_v * final_height  + final_height

    # Make sure the entire focal point is in the crop box
    focal_point_left = focal_point.x - focal_point.width / 2
    focal_point_top = focal_point.y - focal_point.height / 2
    focal_point_right = focal_point.x + focal_point.width / 2
    focal_point_bottom = focal_point.y + focal_point.height / 2

    if left > focal_point_left:
        right -= left - focal_point_left
        left = focal_point_left

    if top > focal_point_top:
        bottom -= top - focal_point_top
        top = focal_point_top

    if right < focal_point_right:
        left += focal_point_right - right;
        right = focal_point_right

    if bottom < focal_point_bottom:
        top += focal_point_bottom - bottom;
        bottom = focal_point_bottom

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
    if len(focal_points) == 1:
        focal_point = focal_points[0]
    else:
        focal_point = combine_focal_points(focal_points)

    return crop_to_point(image_size, crop_size, focal_point)
