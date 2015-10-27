from django import forms
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin.widgets import AdminPageChooser

from wagtail.wagtailcore.models import Site
from wagtail.wagtailredirects.models import Redirect


class RedirectForm(forms.ModelForm):
    site = forms.ModelChoiceField(label=_("From site"), queryset=Site.objects.all(), required=False, empty_label=_("All sites"))

    def __init__(self, *args, **kwargs):
        super(RedirectForm, self).__init__(*args, **kwargs)
        self.fields['redirect_page'].widget = AdminPageChooser()

    required_css_class = "required"

    class Meta:
        model = Redirect
        fields = ('old_path', 'site', 'is_permanent', 'redirect_page', 'redirect_link')
