from django import forms
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


def validate_url(url):
    validator = URLValidator()
    try:
        validator(url)
    except ValidationError:
        raise ValidationError(_("Please enter a valid URL"))


class EmbedForm(forms.Form):
    url = forms.CharField(label=_("URL"), validators=[validate_url])
