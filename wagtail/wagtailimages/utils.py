import os

from PIL import Image

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy  as _


def validate_image_format(f):
    # Check file extension
    extension = os.path.splitext(f.name)[1].lower()[1:]

    if extension == 'jpg':
        extension = 'jpeg'

    if extension not in ['gif', 'jpeg', 'png']:
        raise ValidationError(_("Not a valid image. Please use a gif, jpeg or png file with the correct file extension (*.gif, *.jpg or *.png)."))

    if not f.closed:
        # Open image file
        file_position = f.tell()
        f.seek(0)

        try:
            image = Image.open(f)
        except IOError:
            # Uploaded file is not even an image file (or corrupted)
            raise ValidationError(_("Not a valid image. Please use a gif, jpeg or png file with the correct file extension (*.gif, *.jpg or *.png)."))

        f.seek(file_position)

        # Check that the internal format matches the extension
        # It is possible to upload PSD files if their extension is set to jpg, png or gif. This should catch them out
        if image.format.upper() != extension.upper():
            raise ValidationError(_("Not a valid %s image. Please use a gif, jpeg or png file with the correct file extension (*.gif, *.jpg or *.png).") % (extension.upper()))
