import swapper

from django import forms
from django.utils.translation import ugettext_lazy as _

from wagtail.admin.widgets import AdminPageChooser
from wagtail.core.models import Site


class SiteForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['root_page'].widget = AdminPageChooser(
            choose_one_text=_('Choose a root page'), choose_another_text=_('Choose a different root page')
        )

    required_css_class = "required"

    class Meta:
        model = swapper.load_model("wagtailcore", "Site")
        fields = swapper.load_model("wagtailcore", "Site").admin_form_fields
