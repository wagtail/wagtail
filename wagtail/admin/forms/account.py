import warnings
from contextlib import contextmanager
from functools import partial
from io import BytesIO
from operator import itemgetter

import l18n
import willow
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.db.models.fields import BLANK_CHOICE_DASH
from django.utils.translation import get_language_info
from django.utils.translation import gettext_lazy as _

from wagtail.admin.localization import (
    get_available_admin_languages,
    get_available_admin_time_zones,
)
from wagtail.admin.widgets import SwitchInput
from wagtail.images.image_operations import ImageTransform, ScaleToPercentOperation
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

    @contextmanager
    def create_avatar_context(self, avatar):
        avatar_context = willow.Image.open(avatar)
        yield avatar_context

    def reduce_avatar(self, avatar):
        default_avatar_size = (400, 400)

        with self.create_avatar_context(avatar) as willow_image:
            width, height = willow_image.get_size()

            should_reduce_avatar = (
                width > default_avatar_size[0] or height > default_avatar_size[1]
            )

            if should_reduce_avatar:
                temp_buffer = BytesIO()
                temp_buffer.seek(0)
                original_format = (
                    willow_image.format_name or willow_image.name.split(".")[-1].lower()
                )
                quality = getattr(settings, "WAGTAILIMAGES_AVIF_QUALITY", 80)

                transform = ImageTransform(size=default_avatar_size)
                operation = ScaleToPercentOperation(None, default_avatar_size[0])
                transform = operation.run(transform, avatar)
                clone_img = willow_image.resize(transform.size)

                img_kwargs = {}
                if original_format not in ["ico", "svg", "gif", "png"]:
                    img_kwargs["quality"] = quality
                if original_format in ["jpeg", "png"]:
                    img_kwargs["optimize"] = True

                temp_buffer.seek(0)

                # get the method to save the image as based on its format, pass in the args and call it
                partial(
                    getattr(clone_img, f"save_as_{original_format}"),
                    temp_buffer,
                    **img_kwargs,
                )()

                # wrap the temp file in a File wrapper
                reduced_avatar = File(file=temp_buffer, name=avatar.name)
                return reduced_avatar
        return None

    def save(self, commit=True):
        reduced_avatar = None
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

            # check and reduce cleaned_data avatar if more than the image size bound specified to the bound
            avatar = self.cleaned_data["avatar"]

            # would be none is no operation is performed
            reduced_avatar = self.reduce_avatar(avatar)

        if reduced_avatar is not None:
            object = super().save(commit=False)
            object.avatar = reduced_avatar
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
