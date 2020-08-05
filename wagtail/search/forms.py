from django import forms
from django.utils.translation import gettext_lazy as _


class QueryForm(forms.Form):
    query_string = forms.CharField(label=_("Search term(s)/phrase"),
                                   help_text=_("Enter the full search string to match. An "
                                               "exact match is required for your Promoted Results to be "
                                               "displayed, wildcards are NOT allowed."),
                                   required=True)
