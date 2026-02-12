import io
import os
import warnings

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.translation import get_language_info
from django.utils.translation import gettext_lazy as _
from PIL import Image

from wagtail.admin.localization import (
    get_available_admin_languages,
    get_available_admin_time_zones,
)
from wagtail.admin.widgets import SwitchInput
from wagtail.permissions import page_permission_policy
from wagtail.users.models import UserProfile

User = get_user_model()


class NotificationPreferencesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        permission_policy = page_permission_policy
        if not permission_policy.user_has_permission(self.instance.user, "publish"):
            del self.fields["submitted_notifications"]
        if not permission_policy.user_has_permission(self.instance.user, "change"):
            del self.fields["approved_notifications"]
            del self.fields["rejected_notifications"]
            del self.fields["updated_comments_notifications"]

    class Meta:
        model = UserProfile
        fields = [
            "submitted_notifications",
            "approved_notifications",
            "rejected_notifications",
            "updated_comments_notifications",
        ]
        widgets = {
            "submitted_notifications": SwitchInput(),
            "approved_notifications": SwitchInput(),
            "rejected_notifications": SwitchInput(),
            "updated_comments_notifications": SwitchInput(),
        }


def _get_language_choices():
    language_choices = [
        (lang_code, get_language_info(lang_code)["name_local"])
        for lang_code, lang_name in get_available_admin_languages()
    ]
    server_language = get_language_info(settings.LANGUAGE_CODE)["name_local"]
    default = (
        "",
        _("Use server language: %(language_name)s")
        % {"language_name": server_language},
    )
    return [default] + sorted(
        language_choices,
        key=lambda language_choice: language_choice[1].lower(),
    )


def _get_time_zone_choices():
    return [("", _("Use server time zone"))] + [
        (tz, tz) for tz in get_available_admin_time_zones()
    ]


class LocalePreferencesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if len(get_available_admin_languages()) <= 1:
            del self.fields["preferred_language"]

        if len(get_available_admin_time_zones()) <= 1:
            del self.fields["current_time_zone"]

    preferred_language = forms.ChoiceField(
        required=False, choices=_get_language_choices, label=_("Preferred language")
    )

    current_time_zone = forms.ChoiceField(
        required=False,
        choices=_get_time_zone_choices,
        label=_("Current time zone"),
        widget=forms.Select(
            attrs={
                "data-controller": "w-init w-locale",
                "data-action": "w-init:ready->w-locale#localizeTimeZoneOptions",
                "data-w-locale-server-time-zone-param": settings.TIME_ZONE,
            },
        ),
    )

    class Meta:
        model = UserProfile
        fields = ["preferred_language", "current_time_zone"]


class NameEmailForm(forms.ModelForm):
    first_name = forms.CharField(required=True, label=_("First Name"))
    last_name = forms.CharField(required=True, label=_("Last Name"))
    email = forms.EmailField(required=True, label=_("Email"))

    def __init__(self, *args, **kwargs):
        from wagtail.admin.views.account import email_management_enabled

        super().__init__(*args, **kwargs)

        if not email_management_enabled():
            del self.fields["email"]

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]


class AvatarPreferencesForm(forms.ModelForm):
    avatar = forms.ImageField(label=_("Upload a profile picture"), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_avatar = self.instance.avatar

    def clean_avatar(self):
        file = self.cleaned_data.get("avatar")
        if not file:
            return self._original_avatar

        image = Image.open(file)
        width, height = image.size

        if width <= 400 and height <= 400:
            return file

        target_size = 400

        if width > height:
            new_width = target_size
            new_height = int(height * (target_size / width))
        else:
            new_height = target_size
            new_width = int(width * (target_size / height))

        resized_image = image.resize((new_width, new_height))

        orig_format = image.format or "JPEG"

        output = io.BytesIO()
        resized_image.save(output, format=image.format)
        output.seek(0)

        new_ext = (
            "jpg" if orig_format.upper() in ("JPEG", "JPG") else orig_format.lower()
        )
        content_type = f"image/{'jpeg' if new_ext == 'jpg' else new_ext}"

        base_name, _ = os.path.splitext(file.name)
        filename = f"{base_name}.{new_ext}"

        new_file = InMemoryUploadedFile(
            file=output,
            field_name="avatar",
            name=filename,
            content_type=content_type,
            size=output.getbuffer().nbytes,
            charset=None,
        )

        return new_file

    def save(self, commit=True):
        if (
            commit
            and self._original_avatar
            and (self._original_avatar != self.cleaned_data["avatar"])
        ):
            # Call delete() on the storage backend directly, as calling self._original_avatar.delete()
            # will clear the now-updated field on self.instance too
            try:
                self._original_avatar.storage.delete(self._original_avatar.name)
            except OSError:
                # failure to delete the old avatar shouldn't prevent us from continuing
                warnings.warn(
                    "Failed to delete old avatar file: %s" % self._original_avatar.name
                )
        return super().save(commit=commit)

    class Meta:
        model = UserProfile
        fields = ["avatar"]


class ThemePreferencesForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["theme", "contrast", "density", "keyboard_shortcuts"]
        widgets = {
            "keyboard_shortcuts": SwitchInput(),
        }
