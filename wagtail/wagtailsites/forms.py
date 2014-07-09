from django import forms

from wagtail.wagtailcore.models import Site


class SiteForm(forms.ModelForm):
    required_css_class = "required"

    class Meta:
        model = Site
