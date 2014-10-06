from django import forms

from wagtail.wagtailcore.models import Site


class SiteForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SiteForm, self).__init__(*args, **kwargs)
        self.fields['root_page'].widget = forms.HiddenInput()

    required_css_class = "required"

    class Meta:
        model = Site
        fields = ('hostname', 'port', 'root_page', 'is_default_site')
