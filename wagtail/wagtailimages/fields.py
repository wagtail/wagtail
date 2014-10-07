import os

from PIL import Image

from django.forms.fields import ImageField
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import filesizeformat
from django.conf import settings


def get_max_image_filesize():
    return getattr(settings, 'WAGTAILIMAGES_MAX_UPLOAD_SIZE', 10 * 1024 * 1024)


class WagtailImageField(ImageField):
    default_error_messages = {
        'invalid_image': _(
            "Not a supported image type. Please use a gif, jpeg or png file "
            "with the correct file extension (*.gif, *.jpg or *.png)."
        ),
        'file_too_large': _(
            "This file is too big (%s). Image files must not exceed %s."
        ),
    }

    def check_image_file_format(self, f):
        # Check file extension
        extension = os.path.splitext(f.name)[1].lower()[1:]

        if extension == 'jpg':
            extension = 'jpeg'

        if extension not in ['gif', 'jpeg', 'png']:
            raise ValidationError(self.error_messages['invalid_image'], code='invalid_image')

        if hasattr(f, 'image'):
            # Django 1.8 annotates the file object with the PIL image
            image = f.image
        elif not f.closed:
            # Open image file
            file_position = f.tell()
            f.seek(0)

            try:
                image = Image.open(f)
            except IOError:
                # Uploaded file is not even an image file (or corrupted)
                raise ValidationError(self.error_messages['invalid_image'], code='invalid_image')

            f.seek(file_position)
        else:
            # Couldn't get the PIL image, skip checking the internal file format
            return

        # Check that the internal format matches the extension
        # It is possible to upload PSD files if their extension is set to jpg, png or gif. This should catch them out
        if image.format.upper() != extension.upper():
            raise ValidationError(self.error_messages['invalid_image'], code='invalid_image')

    def check_image_file_size(self, f):
        # Get max size
        max_size = get_max_image_filesize()

        # Upload size checking can be disabled by setting max upload size to None
        if max_size is None:
            return

        # Check the filesize
        if f.size > max_size:
            raise ValidationError(self.error_messages['file_too_large'] % (
                filesizeformat(f.size),
                filesizeformat(max_size),
            ), code='file_too_large')

    def to_python(self, data):
        f = super(WagtailImageField, self).to_python(data)

        self.check_image_file_format(f)
        self.check_image_file_size(f)

        return f
