from django import forms
from django.core.validators import URLValidator
from django.utils.translation import ugettext_lazy as _


class EmbedForm(forms.Form):
    url = forms.CharField(
        label=_("URL"), validators=[URLValidator(message=_("Please enter a valid URL"))]
    )
