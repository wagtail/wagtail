from django import forms
from django.utils.translation import gettext_lazy as _

from wagtail.admin.widgets import AdminPageChooser
from wagtail.models import Site


class SiteForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["root_page"].widget = AdminPageChooser(
            choose_one_text=_("Choose a root page"),
            choose_another_text=_("Choose a different root page"),
            show_clear_link=False,
        )

    required_css_class = "required"

    class Meta:
        model = Site
        fields = ("hostname", "port", "site_name", "root_page", "is_default_site")
