from django import forms
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError


def validate_url(url):
    validator = URLValidator()
    try:
        validator(url)
    except ValidationError:
        raise ValidationError("Please enter a valid URL")


class EmbedForm(forms.Form):
    url = forms.CharField(label="URL", validators=[validate_url])
