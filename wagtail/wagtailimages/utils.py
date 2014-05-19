import os

from PIL import Image

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy  as _
from django.conf import settings


def validate_image_format(f):
    # Check file extension
    extension = os.path.splitext(f.name)[1].lower()[1:]

    if extension == 'jpg':
        extension = 'jpeg'

    if extension not in ['gif', 'jpeg', 'png']:
        raise ValidationError(_("Not a valid image. Please use a gif, jpeg or png file with the correct file extension."))

    if f.closed:
        # Reopen the file
        file = open(os.path.join(settings.MEDIA_ROOT, f.name), 'rb')
        close = True
    else:
        # Seek to first byte but save position to be restored later
        file_position = f.tell()
        f.seek(0)
        file = f
        close = False

    # Open image file
    image = Image.open(file)

    # Check that the internal format matches the extension
    if image.format.upper() != extension.upper():
        raise ValidationError(_("Not a valid %s image. Please use a gif, jpeg or png file with the correct file extension.") % (extension.upper()))

    # Close/restore file
    if close:
        file.close()
    else:
        f.seek(file_position)
