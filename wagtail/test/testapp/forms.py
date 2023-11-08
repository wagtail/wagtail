from django import forms
from django.contrib.auth import get_user_model

from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.admin.widgets import AdminDateInput


class ValidatedPageForm(WagtailAdminPageForm):
    def clean_foo(self):
        if "foo" not in self.cleaned_data:
            return

        value = self.cleaned_data["foo"]
        if self.for_user.is_superuser and value == "superbar":
            pass
        elif value != "bar":
            raise forms.ValidationError("Field foo must be bar")
        return value


class FormClassAdditionalFieldPageForm(WagtailAdminPageForm):
    code = forms.CharField(help_text="Enter SMS authentication code", max_length=5)

    def clean(self):
        cleaned_data = super().clean()

        # validate the user's code with our code check
        code = cleaned_data["code"]
        if not code:
            raise forms.ValidationError("Code is not valid")

        return cleaned_data


class AdminStarDateInput(AdminDateInput):
    # Media definitions defined as `class Media:` should be merged into
    # the media of the parent class
    class Media:
        js = ["vendor/star_date.js"]


class FavouriteColourForm(forms.ModelForm):
    # for testing that form media from account settings panels gets included
    # on the form page
    class Meta:
        model = get_user_model()
        fields = []

    class Media:
        js = ["vendor/colorpicker.js"]
