from django import forms

from wagtail.wagtailadmin.widgets import AdminPageChooser

from wagtail.wagtailredirects import models


class RedirectForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(RedirectForm, self).__init__(*args, **kwargs)
        self.fields['redirect_page'].widget = AdminPageChooser()

    required_css_class = "required"

    class Meta:
        model = models.Redirect
        fields = ('old_path', 'is_permanent', 'redirect_page', 'redirect_link')
