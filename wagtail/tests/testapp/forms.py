from django import forms

from wagtail.wagtailadmin.forms import WagtailAdminPageForm


class ValidatedPageForm(WagtailAdminPageForm):
    def clean_foo(self):
        if 'foo' not in self.cleaned_data:
            return

        value = self.cleaned_data['foo']
        if value != 'bar':
            raise forms.ValidationError('Field foo must be bar')
        return value
