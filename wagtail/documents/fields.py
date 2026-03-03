from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms.fields import FileField
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _


class WagtailDocumentField(FileField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Get max upload size from settings, default is None (no limit)
        self.max_upload_size = getattr(settings, "WAGTAILDOCS_MAX_UPLOAD_SIZE", None)
        self.max_upload_size_text = filesizeformat(self.max_upload_size)

        # Help text
        if self.max_upload_size is not None:
            self.help_text = _(
                "Maximum filesize: %(max_upload_size)s."
            ) % {"max_upload_size": self.max_upload_size_text}
        else:
            self.help_text = ""
            
        # Error messages
        # Translation placeholders should all be interpolated at the same time to avoid escaping,
        # either right now if all values are known, otherwise when used.
        self.error_messages["file_too_large"] = _(
            "This file is too big (%(file_size)s). Maximum filesize %(max_filesize)s."
        )
        self.error_messages["file_too_large_unknown_size"] = _(
            "This file is too big. Maximum filesize %(max_filesize)s."
        ) % {"max_filesize": self.max_upload_size_text}


    def check_document_file_size(self, f):
        # Upload size checking can be disabled by setting max upload size to None
        if self.max_upload_size is None:
            return

        # Check the filesize
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