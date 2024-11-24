import warnings
from operator import itemgetter

import l18n
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.fields import BLANK_CHOICE_DASH
from django.utils.translation import get_language_info
from django.utils.translation import gettext_lazy as _

from wagtail.admin.localization import (
    get_available_admin_languages,
    get_available_admin_time_zones,
)
from wagtail.admin.widgets import SwitchInput
from wagtail.permissions import page_permission_policy
from wagtail.users.models import UserProfile
from wagtail.utils.utils import reduce_image_size

User = get_user_model()

WAGTAIL_USER_PROFILE_IMAGE_SIZE_BOUND = getattr(settings, "WAGTAIL_USER_PROFILE_IMAGE_SIZE_BOUND", 1024)


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
    return sorted(
        BLANK_CHOICE_DASH + language_choices,
        key=lambda language_choice: language_choice[1].lower(),
    )


def _get_time_zone_choices():
    time_zones = [
        (tz, str(l18n.tz_fullnames.get(tz, tz)))
        for tz in get_available_admin_time_zones()
    ]
    time_zones.sort(key=itemgetter(1))
    return BLANK_CHOICE_DASH + time_zones


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
        required=False, choices=_get_time_zone_choices, label=_("Current time zone")
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

    def save(self, commit=True):
        updated_avatar = None
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

            #check and reduce cleaned_data avatar if more than the image size bound specified to the bound
            avatar = self.cleaned_data["avatar"]
            avatar_size = avatar.size/1024
            if avatar_size > WAGTAIL_USER_PROFILE_IMAGE_SIZE_BOUND:
                updated_avatar = reduce_image_size(
                    avatar=avatar,
                    size_bound=WAGTAIL_USER_PROFILE_IMAGE_SIZE_BOUND
                )

        if updated_avatar is not None:
            object = super().save(commit=False)
            object.avatar = updated_avatar
            object.save()
        else:
            super().save(commit=commit)

    class Meta:
        model = UserProfile
        fields = ["avatar"]


class ThemePreferencesForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["theme", "contrast", "density"]
