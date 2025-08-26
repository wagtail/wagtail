import hmac

from django import forms
from django.utils.encoding import force_bytes
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy


class PasswordViewRestrictionForm(forms.Form):
    password = forms.CharField(
        label=gettext_lazy("Password"), widget=forms.PasswordInput
    )
    return_url = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        self.restriction = kwargs.pop("instance")
        super().__init__(*args, **kwargs)

    def clean_password(self):
        data = force_bytes(self.cleaned_data["password"])
        password = force_bytes(self.restriction.password)
        if not hmac.compare_digest(data, password):
            raise forms.ValidationError(
                _("The password you have entered is not correct. Please try again.")
            )

        return data


class TaskStateCommentForm(forms.Form):
    comment = forms.CharField(
        label=_("Comment"), required=False, widget=forms.Textarea({"rows": 2})
    )
