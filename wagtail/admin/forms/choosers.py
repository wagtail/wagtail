from django import forms
from django.core import validators
from django.forms.widgets import TextInput
from django.utils.translation import ugettext_lazy


class URLOrAbsolutePathValidator(validators.URLValidator):
    @staticmethod
    def is_absolute_path(value):
        return value.startswith('/')

    def __call__(self, value):
        if URLOrAbsolutePathValidator.is_absolute_path(value):
            return None
        else:
            return super().__call__(value)


class URLOrAbsolutePathField(forms.URLField):
    widget = TextInput
    default_validators = [URLOrAbsolutePathValidator()]

    def to_python(self, value):
        if not URLOrAbsolutePathValidator.is_absolute_path(value):
            value = super().to_python(value)
        return value


class ExternalLinkChooserForm(forms.Form):
    url = URLOrAbsolutePathField(required=True, label=ugettext_lazy("URL"))
    link_text = forms.CharField(required=False)


class EmailLinkChooserForm(forms.Form):
    email_address = forms.EmailField(required=True)
    link_text = forms.CharField(required=False)
