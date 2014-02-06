from PIL import Image


def resize(image, size):
    """
    resize image to the requested size, using highest quality settings
    (antialiasing enabled, converting to true colour if required)
    """
    if image.mode in ['1', 'P']:
        image = image.convert('RGB')

    return image.resize(size, Image.ANTIALIAS)


def crop_to_centre(image, size):
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


def resize_to_max(image, size):
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

    return resize(image, final_size)


def resize_to_min(image, size):
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

    return resize(image, final_size)


def resize_to_width(image, target_width):
    """
    Resize image down to the given width, preserving aspect ratio.
    Will leave image unchanged if it's already within that width.
    """
    (original_width, original_height) = image.size

    if original_width <= target_width:
        return image

    scale = float(target_width) / original_width

    final_size = (target_width, int(original_height * scale))

    return resize(image, final_size)


def resize_to_height(image, target_height):
    """
    Resize image down to the given height, preserving aspect ratio.
    Will leave image unchanged if it's already within that height.
    """
    (original_width, original_height) = image.size

    if original_height <= target_height:
        return image

    scale = float(target_height) / original_height

    final_size = (int(original_width * scale), target_height)

    return resize(image, final_size)


def resize_to_fill(image, size):
    """
    Resize down and crop image to fill the given dimensions. Most suitable for thumbnails.
    (The final image will match the requested size, unless one or the other dimension is
    already smaller than the target size)
    """
    resized_image = resize_to_min(image, size)
    return crop_to_centre(resized_image, size)
