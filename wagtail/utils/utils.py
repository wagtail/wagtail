from collections.abc import Mapping
from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile
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


def reduce_image_size(avatar, size_bound, max_dimensions=(400, 400)):
    """
    Reduce an image's file size to a size_bound in kilobytes.

    :param avatar: The original image gotten from the image field of the form
    :param size_bound: Desired size in KB
    :param max_dimensions: Maximum dimensions for resizing
    """
    temp_buffer = BytesIO()
    kilobyte = 1024
    with Image.open(avatar) as img:
        if img.mode == "RGBA":
            img = img.convert("RGB")
        img.thumbnail(max_dimensions, Image.LANCZOS)
        img_ext = avatar.name.split(".")[-1]

        quality = 95
        step = 5

        while quality > 10:
            temp_buffer.seek(0)
            img.save(
                temp_buffer,
                format="JPEG" if img_ext != "png" else "PNG",
                quality=quality,
                optimize=True,
            )
            file_size_kb = temp_buffer.tell() / kilobyte

            if file_size_kb <= size_bound:
                break

            quality -= step

        temp_buffer.seek(0)
        in_mem_avatar = InMemoryUploadedFile(
            file=temp_buffer,
            field_name="ImageField",
            name=avatar.name,
            content_type="image/jpeg" if img_ext != "png" else "PNG",
            size=temp_buffer.tell(),
            charset=None,
        )
        return in_mem_avatar
