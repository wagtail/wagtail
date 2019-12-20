from django import forms
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy


class SearchForm(forms.Form):
    def __init__(self, *args, **kwargs):
        placeholder = kwargs.pop('placeholder', _("Search"))
        super().__init__(*args, **kwargs)
        self.fields['q'].widget.attrs = {'placeholder': placeholder}

    q = forms.CharField(label=ugettext_lazy("Search term"), widget=forms.TextInput())
