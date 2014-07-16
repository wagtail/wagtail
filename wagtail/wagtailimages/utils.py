import os
import re

from PIL import Image

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy  as _


def validate_image_format(f):
    # Check file extension
    extension = os.path.splitext(f.name)[1].lower()[1:]

    if extension == 'jpg':
        extension = 'jpeg'

    if extension not in ['gif', 'jpeg', 'png']:
        raise ValidationError(_("Not a valid image. Please use a gif, jpeg or png file with the correct file extension."))

    if not f.closed:
        # Open image file
        file_position = f.tell()
        f.seek(0)
        image = Image.open(f)
        f.seek(file_position)

        # Check that the internal format matches the extension
        if image.format.upper() != extension.upper():
            raise ValidationError(_("Not a valid %s image. Please use a gif, jpeg or png file with the correct file extension.") % (extension.upper()))


class InvalidFilterSpecError(RuntimeError):
    pass


# TODO: Cache results from this method in something like Python 3.2s LRU cache (available in Django 1.7 as django.utils.lru_cache)
def parse_filter_spec(filter_spec):
    # parse the spec string and save the results to
    # self.method_name and self.method_arg. There are various possible
    # formats to match against:
    # 'original'
    # 'width-200'
    # 'max-320x200'

    OPERATION_NAMES = {
        'max': 'resize_to_max',
        'min': 'resize_to_min',
        'width': 'resize_to_width',
        'height': 'resize_to_height',
        'fill': 'resize_to_fill',
        'original': 'no_operation',
    }

    # original
    if filter_spec == 'original':
        return OPERATION_NAMES['original'], None

    # width/height
    match = re.match(r'(width|height)-(\d+)$', filter_spec)
    if match:
        return OPERATION_NAMES[match.group(1)], int(match.group(2))

    # max/min/fill
    match = re.match(r'(max|min|fill)-(\d+)x(\d+)$', filter_spec)
    if match:
        width = int(match.group(2))
        height = int(match.group(3))
        return OPERATION_NAMES[match.group(1)], (width, height)

    raise InvalidFilterSpecError(filter_spec)
