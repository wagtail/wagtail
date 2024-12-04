from collections.abc import Mapping
from django.core.files import File
from io import BytesIO
from PIL import Image


def deep_update(source, overrides):
    """Update a nested dictionary or similar mapping.

    Modify ``source`` in place.
    """
    for key, value in overrides.items():
        if isinstance(value, Mapping) and value:
            returned = deep_update(source.get(key, {}), value)
            source[key] = returned
        else:
            source[key] = overrides[key]
    return source


def flatten_choices(choices):
    """
    Convert potentially grouped choices into a flat dict of choices.

    flatten_choices([(1, '1st'), (2, '2nd')]) -> {1: '1st', 2: '2nd'}
    flatten_choices([('Group', [(1, '1st'), (2, '2nd')])]) -> {1: '1st', 2: '2nd'}
    flatten_choices({'Group': {'1': '1st', '2': '2nd'}}) -> {'1': '1st', '2': '2nd'}
    """
    ret = {}

    to_unpack = choices.items() if isinstance(choices, dict) else choices

    for key, value in to_unpack:
        if isinstance(value, (list, tuple)):
            # grouped choices (category, sub choices)
            for sub_key, sub_value in value:
                ret[str(sub_key)] = sub_value
        elif isinstance(value, (dict)):
            # grouped choices using dict (category, sub choices)
            for sub_key, sub_value in value.items():
                ret[str(sub_key)] = sub_value
        else:
            # choice (key, display value)
            ret[str(key)] = value
    return ret


def reduce_image_dimension(image, max_dimensions=(400, 400)):
    """
    Reduce an image's dimension to specified max_dimesions if lower
    higher than the provided max_dimensions.

    :param image: The image to be computed on. Expects an image object
    :param max_dimensions: Maximum dimensions for resizing (width: int, height: int)
    """
    img_ext = image.name.split(".")[-1]

    with Image.open(image) as img:
        width, height = img.width, img.height
        if width <= max_dimensions[0] and height <= max_dimensions[1]:
            return image

        temp_buffer = BytesIO()
        if img.mode == "RGBA":
            img = img.convert("RGB")
        img.thumbnail(max_dimensions, Image.LANCZOS)
        temp_buffer.seek(0)
        img.save(
            temp_buffer,
            format=img.format or img_ext.upper(),
            optimize=True,
        )

        temp_buffer.seek(0)
        image_file = File(
            file=temp_buffer,
            name=image.name,
        )
        return image_file
