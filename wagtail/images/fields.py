import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms.fields import ImageField
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _

ALLOWED_EXTENSIONS = ['gif', 'jpg', 'jpeg', 'png']
SUPPORTED_FORMATS_TEXT = _("GIF, JPEG, PNG")


class WagtailImageField(ImageField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Get max upload size from settings
        self.max_upload_size = getattr(settings, 'WAGTAILIMAGES_MAX_UPLOAD_SIZE', 10 * 1024 * 1024)
        max_upload_size_text = filesizeformat(self.max_upload_size)

        # Help text
        if self.max_upload_size is not None:
            self.help_text = _(
                "Supported formats: %(supported_formats)s. Maximum filesize: %(max_upload_size)s."
            ) % {
                'supported_formats': SUPPORTED_FORMATS_TEXT,
                'max_upload_size': max_upload_size_text,
            }
        else:
            self.help_text = _(
                "Supported formats: %(supported_formats)s."
            ) % {
                'supported_formats': SUPPORTED_FORMATS_TEXT,
            }

        # Error messages
        self.error_messages['invalid_image'] = _(
            "Not a supported image format. Supported formats: %s."
        ) % SUPPORTED_FORMATS_TEXT

        self.error_messages['invalid_image_known_format'] = _(
            "Not a valid %s image."
        )

        self.error_messages['file_too_large'] = _(
            "This file is too big (%%s). Maximum filesize %s."
        ) % max_upload_size_text

        self.error_messages['file_too_large_unknown_size'] = _(
            "This file is too big. Maximum filesize %s."
        ) % max_upload_size_text

    def check_image_file_format(self, f):
        # Check file extension
        extension = os.path.splitext(f.name)[1].lower()[1:]

        if extension not in ALLOWED_EXTENSIONS:
            raise ValidationError(self.error_messages['invalid_image'], code='invalid_image')

        image_format = extension.upper()
        if image_format == 'JPG':
            image_format = 'JPEG'

        internal_image_format = f.image.format.upper()
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
        if self.max_upload_size is None:
            return

        # Check the filesize
        if f.size > self.max_upload_size:
            raise ValidationError(self.error_messages['file_too_large'] % (
                filesizeformat(f.size),
            ), code='file_too_large')

    def to_python(self, data):
        f = super().to_python(data)

        if f is not None:
            self.check_image_file_size(f)
            self.check_image_file_format(f)

        return f
