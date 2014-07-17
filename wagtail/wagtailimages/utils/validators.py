import os

from PIL import Image

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


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
