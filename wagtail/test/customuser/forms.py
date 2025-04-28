from django import forms

from wagtail.users.forms import UserCreationForm, UserEditForm


class CustomUserCreationForm(UserCreationForm):
    country = forms.CharField(required=True, label="Country")
    attachment = forms.FileField(required=True, label="Attachment")

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields | {"country", "attachment"}


class CustomUserEditForm(UserEditForm):
    country = forms.CharField(required=True, label="Country")
    attachment = forms.FileField(required=True, label="Attachment")

    class Meta(UserEditForm.Meta):
        fields = UserEditForm.Meta.fields | {"country", "attachment"}
