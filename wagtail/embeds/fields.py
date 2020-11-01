from django import forms
from django.core.validators import URLValidator
from django.db.models import TextField
from django.utils.translation import gettext_lazy as _


class URLField(TextField):
    default_validators = [URLValidator()]
    description = _("URL")

    def formfield(self, **kwargs):
        # As with CharField, this will cause URL validation to be performed
        # twice.
        return super().formfield(**{
            'form_class': forms.URLField,
            **kwargs,
        })
