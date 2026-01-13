import os
import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

from wagtail.admin.localization import get_available_admin_languages


def upload_avatar_to(instance, filename):
    filename, ext = os.path.splitext(filename)
    return os.path.join(
        "avatar_images",
        "avatar_{uuid}_{filename}{ext}".format(
            uuid=uuid.uuid4(), filename=filename, ext=ext
        ),
    )


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wagtail_userprofile",
    )

    submitted_notifications = models.BooleanField(
        verbose_name=_("submitted notifications"),
        default=True,
        help_text=_("Receive notification when a page is submitted for moderation"),
    )

    approved_notifications = models.BooleanField(
        verbose_name=_("approved notifications"),
        default=True,
        help_text=_("Receive notification when your page edit is approved"),
    )

    rejected_notifications = models.BooleanField(
        verbose_name=_("rejected notifications"),
        default=True,
        help_text=_("Receive notification when your page edit is rejected"),
    )

    updated_comments_notifications = models.BooleanField(
        verbose_name=_("updated comments notifications"),
        default=True,
        help_text=_(
            "Receive notification when comments have been created, resolved, or deleted on a page that you have subscribed to receive comment notifications on"
        ),
    )

    preferred_language = models.CharField(
        verbose_name=_("preferred language"),
        max_length=10,
        help_text=_("Select language for the admin"),
        default="",
    )

    current_time_zone = models.CharField(
        verbose_name=_("current time zone"),
        max_length=40,
        help_text=_("Select your current time zone"),
        default="",
    )

    avatar = models.ImageField(
        verbose_name=_("profile picture"),
        upload_to=upload_avatar_to,
        blank=True,
    )

    dismissibles = models.JSONField(default=dict, blank=True)

    class AdminColorThemes(models.TextChoices):
        SYSTEM = "system", _("System default")
        LIGHT = "light", _("Light")
        DARK = "dark", _("Dark")

    theme = models.CharField(
        verbose_name=_("admin theme"),
        choices=AdminColorThemes.choices,
        default=AdminColorThemes.SYSTEM,
        max_length=40,
    )

    class AdminContrastThemes(models.TextChoices):
        SYSTEM = "system", _("System default")
        MORE_CONTRAST = "more_contrast", _("More contrast")

    contrast = models.CharField(
        verbose_name=_("contrast"),
        choices=AdminContrastThemes.choices,
        default=AdminContrastThemes.SYSTEM,
        max_length=40,
    )

    class AdminDensityThemes(models.TextChoices):
        DEFAULT = "default", _("Default")
        SNUG = "snug", _("Snug")

    density = models.CharField(
        # Translators: "Density" is the term used to describe the amount of space between elements in the user interface
        verbose_name=_("density"),
        choices=AdminDensityThemes.choices,
        default=AdminDensityThemes.DEFAULT,
        max_length=40,
    )

    keyboard_shortcuts = models.BooleanField(
        verbose_name=_("Keyboard shortcuts"),
        default=True,
        help_text=_("Enable custom keyboard shortcuts specific to Wagtail."),
    )

    @classmethod
    def get_for_user(cls, user):
        return cls.objects.get_or_create(user=user)[0]

    def get_preferred_language(self):
        if self.preferred_language:
            return self.preferred_language
        if (language := get_language()) in dict(get_available_admin_languages()):
            return language
        return settings.LANGUAGE_CODE

    def get_current_time_zone(self):
        return self.current_time_zone or settings.TIME_ZONE

    def __str__(self):
        return self.user.get_username()

    class Meta:
        verbose_name = _("user profile")
        verbose_name_plural = _("user profiles")
