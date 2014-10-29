import os

from PIL import Image

from django.forms.fields import ImageField
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import filesizeformat
from django.conf import settings


ALLOWED_EXTENSIONS = ['gif', 'jpg', 'jpeg', 'png']
SUPPORTED_FORMATS_TEXT = _("GIF, JPEG, PNG")

INVALID_IMAGE_ERROR = _(
    "Not a supported image format. Supported formats: %s."
) % SUPPORTED_FORMATS_TEXT

INVALID_IMAGE_KNOWN_FORMAT_ERROR = _(
    "Not a valid %s image."
)

MAX_UPLOAD_SIZE = getattr(settings, 'WAGTAILIMAGES_MAX_UPLOAD_SIZE', 10 * 1024 * 1024)

if MAX_UPLOAD_SIZE is not None:
    MAX_UPLOAD_SIZE_TEXT = filesizeformat(MAX_UPLOAD_SIZE)

    FILE_TOO_LARGE_ERROR = _(
        "This file is too big. Maximum filesize %s."
    ) % (MAX_UPLOAD_SIZE_TEXT, )

    FILE_TOO_LARGE_KNOWN_SIZE_ERROR = _(
        "This file is too big (%%s). Maximum filesize %s."
    ) % (MAX_UPLOAD_SIZE_TEXT, )

    IMAGE_FIELD_HELP_TEXT = _(
        "Supported formats: %s. Maximum filesize: %s."
    ) % (SUPPORTED_FORMATS_TEXT, MAX_UPLOAD_SIZE_TEXT, )
else:
    MAX_UPLOAD_SIZE_TEXT = ""
    FILE_TOO_LARGE_ERROR = ""
    FILE_TOO_LARGE_KNOWN_SIZE_ERROR = ""

    IMAGE_FIELD_HELP_TEXT = _(
        "Supported formats: %s."
    ) % (SUPPORTED_FORMATS_TEXT, )


class WagtailImageField(ImageField):
    default_error_messages = {
        'invalid_image': INVALID_IMAGE_ERROR,
        'invalid_image_known_format': INVALID_IMAGE_KNOWN_FORMAT_ERROR,
        'file_too_large': FILE_TOO_LARGE_KNOWN_SIZE_ERROR,
    }

    def __init__(self, *args, **kwargs):
        super(WagtailImageField, self).__init__(*args, **kwargs)

        self.help_text = IMAGE_FIELD_HELP_TEXT

    def check_image_file_format(self, f):
        # Check file extension
        extension = os.path.splitext(f.name)[1].lower()[1:]

        if extension not in ALLOWED_EXTENSIONS:
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
                raise ValidationError(self.error_messages['invalid_image_known_format'],
                    code='invalid_image_known_format')

            f.seek(file_position)
        else:
            # Couldn't get the PIL image, skip checking the internal file format
            return

        image_format = extension.upper()
        if image_format == 'JPG':
            image_format = 'JPEG'

        internal_image_format = image.format.upper()
        if internal_image_format == 'MPO':
            internal_image_format = 'JPEG'

        # Check that the internal format matches the extension
        # It is possible to upload PSD files if their extension is set to jpg, png or gif. This should catch them out
        if internal_image_format != image_format:
            raise ValidationError(self.error_messages['invalid_image_known_format'] % (
                image_format,
            ), code='invalid_image_known_format')

    def check_image_file_size(self, f):
        # Upload size checking can be disabled by setting max upload size to None
        if MAX_UPLOAD_SIZE is None:
            return

        # Check the filesize
        if f.size > MAX_UPLOAD_SIZE:
            raise ValidationError(self.error_messages['file_too_large'] % (
                filesizeformat(f.size),
            ), code='file_too_large')

    def to_python(self, data):
        f = super(WagtailImageField, self).to_python(data)

        if f is not None:
            self.check_image_file_size(f)
            self.check_image_file_format(f)

        return f
