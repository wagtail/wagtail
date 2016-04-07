from __future__ import absolute_import, unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin.widgets import AdminPageChooser
from wagtail.wagtailcore.models import Site
from wagtail.wagtailredirects.models import Redirect


class RedirectForm(forms.ModelForm):
    site = forms.ModelChoiceField(
        label=_("From site"), queryset=Site.objects.all(), required=False, empty_label=_("All sites")
    )

    def __init__(self, *args, **kwargs):
        super(RedirectForm, self).__init__(*args, **kwargs)
        self.fields['redirect_page'].widget = AdminPageChooser()

    required_css_class = "required"

    def clean(self):
        """
        The unique_together condition on the model is ignored if site is None, so need to
        check for duplicates manually
        """
        cleaned_data = super(RedirectForm, self).clean()

        if cleaned_data.get('site') is None:
            old_path = cleaned_data.get('old_path')
            if old_path is None:
                # cleaned_data['old_path'] is empty because it has already failed validation,
                # so don't bother with our duplicate test
                return

            old_path = Redirect.normalise_path(old_path)
            duplicates = Redirect.objects.filter(old_path=old_path, site__isnull=True)
            if self.instance.pk:
                duplicates = duplicates.exclude(id=self.instance.pk)

            if duplicates:
                raise forms.ValidationError(_("A redirect with this path already exists."))

    class Meta:
        model = Redirect
        fields = ('old_path', 'site', 'is_permanent', 'redirect_page', 'redirect_link')
