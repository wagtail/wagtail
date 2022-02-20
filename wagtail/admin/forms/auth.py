from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm
from django.contrib.auth.forms import PasswordResetForm as DjangoPasswordResetForm
from django.utils.translation import gettext_lazy


class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=254, widget=forms.TextInput())

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": gettext_lazy("Enter password"),
            }
        )
    )

    remember = forms.BooleanField(required=False)

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request=request, *args, **kwargs)
        self.fields["username"].widget.attrs["placeholder"] = (
            gettext_lazy("Enter your %s") % self.username_field.verbose_name
        )

    @property
    def extra_fields(self):
        for field_name in self.fields.keys():
            if field_name not in ["username", "password", "remember"]:
                yield field_name, self[field_name]


class PasswordResetForm(DjangoPasswordResetForm):
    email = forms.EmailField(
        label=gettext_lazy("Enter your email address to reset your password"),
        max_length=254,
        required=True,
    )


class PasswordChangeForm(DjangoPasswordChangeForm):
    """
    Since this is displayed as part of a larger form, this differs from the vanilla Django
    PasswordChangeForm as follows:
    * the old-password field is not auto-focused
    * Fields are not marked as required
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            del self.fields["old_password"].widget.attrs["autofocus"]
        except KeyError:
            pass

        self.fields["old_password"].required = False
        self.fields["new_password1"].required = False
        self.fields["new_password2"].required = False
