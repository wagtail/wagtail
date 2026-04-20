from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms.fields import FileField
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _


def get_allowed_document_extensions():
    return getattr(settings, "WAGTAILDOCS_EXTENSIONS", None)


class WagtailDocumentField(FileField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.allowed_document_extensions = get_allowed_document_extensions()
        self.max_upload_size = getattr(settings, "WAGTAILDOCS_MAX_UPLOAD_SIZE", None)
        self.max_upload_size_text = filesizeformat(self.max_upload_size)

        if self.allowed_document_extensions is not None:
            self.supported_formats_text = ", ".join(
                self.allowed_document_extensions
            ).upper()
        else:
            self.supported_formats_text = None

        hints = []
        if self.supported_formats_text:
            hints.append(
                _("Supported formats: %(supported_formats)s.") % {
                    "supported_formats": self.supported_formats_text,
                }
            )
        if self.max_upload_size is not None:
            hints.append(
                _("Maximum filesize: %(max_upload_size)s.") % {
                    "max_upload_size": self.max_upload_size_text,
                }
            )
        self.help_text = " ".join(hints)

        if self.supported_formats_text:
            self.error_messages["invalid_document_extension"] = _(
                "Not a supported document format. Supported formats: %(supported_formats)s."
            ) % {"supported_formats": self.supported_formats_text}
        else:
            self.error_messages["invalid_document_extension"] = _(
                "Not a supported document format."
            )

        self.error_messages["file_too_large"] = _(
            "This file is too big (%(file_size)s). Maximum filesize %(max_filesize)s."
        )
        self.error_messages["file_too_large_unknown_size"] = _(
            "This file is too big. Maximum filesize %(max_filesize)s."
        ) % {"max_filesize": self.max_upload_size_text}

    def check_document_file_size(self, f):
        if self.max_upload_size is None:
            return

        if f.size > self.max_upload_size:
            raise ValidationError(
                self.error_messages["file_too_large"]
                % {
                    "file_size": filesizeformat(f.size),
                    "max_filesize": self.max_upload_size_text,
                },
                code="file_too_large",
            )

    def to_python(self, data):
        f = super().to_python(data)
        if f is None:
            return None
        self.check_document_file_size(f)
        return f
