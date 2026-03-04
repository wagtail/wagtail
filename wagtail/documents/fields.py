import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms.fields import FileField
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _


def get_allowed_document_extensions():
    """Return the configured allow-list of document extensions.

    If WAGTAILDOCS_EXTENSIONS is unset or empty, documents of all extensions are
    permitted (consistent with the existing model-level behaviour).
    """

    allowed_extensions = getattr(settings, "WAGTAILDOCS_EXTENSIONS", None)
    if not allowed_extensions:
        return []
    return [ext.lower().lstrip(".") for ext in allowed_extensions]


class WagtailDocumentField(FileField):
    def __init__(self, *args, **kwargs):
        self.allowed_document_extensions = get_allowed_document_extensions()

        super().__init__(*args, **kwargs)

       
        self.max_upload_size = getattr(
            settings, "WAGTAILDOCS_MAX_UPLOAD_SIZE", 10 * 1024 * 1024
        )
        self.max_upload_size_text = (
            filesizeformat(self.max_upload_size)
            if self.max_upload_size is not None
            else None
        )

        self.supported_formats_text = (
            ", ".join(self.allowed_document_extensions).upper()
            if self.allowed_document_extensions
            else None
        )

        # Help text
        if self.supported_formats_text and self.max_upload_size is not None:
            self.help_text = _(
                "Supported formats: %(supported_formats)s. Maximum filesize: %(max_upload_size)s."
            ) % {
                "supported_formats": self.supported_formats_text,
                "max_upload_size": self.max_upload_size_text,
            }
        elif self.supported_formats_text:
            self.help_text = _("Supported formats: %(supported_formats)s.") % {
                "supported_formats": self.supported_formats_text,
            }
        elif self.max_upload_size is not None:
            self.help_text = _("Maximum filesize: %(max_upload_size)s.") % {
                "max_upload_size": self.max_upload_size_text,
            }

       
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

        if self.max_upload_size is not None:
            self.error_messages["file_too_large_unknown_size"] = _(
                "This file is too big. Maximum filesize %(max_filesize)s."
            ) % {"max_filesize": self.max_upload_size_text}

    def check_document_file_extension(self, f):
        if not self.allowed_document_extensions:
            return

        extension = os.path.splitext(f.name)[1].lower().lstrip(".")
        if extension not in self.allowed_document_extensions:
            raise ValidationError(
                self.error_messages["invalid_document_extension"],
                code="invalid_document_extension",
            )

    def check_document_file_size(self, f):
       
        if self.max_upload_size is None:
            return

        try:
            file_size = f.size
        except Exception as exc:  # noqa: BLE001
            raise ValidationError(
                self.error_messages["file_too_large_unknown_size"],
                code="file_too_large",
            ) from exc

        if file_size > self.max_upload_size:
            raise ValidationError(
                self.error_messages["file_too_large"]
                % {
                    "file_size": filesizeformat(file_size),
                    "max_filesize": self.max_upload_size_text,
                },
                code="file_too_large",
            )

    def to_python(self, data):
        f = super().to_python(data)
        if f is None:
            return None

        self.check_document_file_size(f)
        self.check_document_file_extension(f)
        return f
