import os
import uuid

from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _


def upload_avatar_to(instance, filename):
    filename, ext = os.path.splitext(filename)
    return os.path.join(
        'avatar_images',
        'avatar_{uuid}_{filename}{ext}'.format(
            uuid=uuid.uuid4(), filename=filename, ext=ext)
    )


class UserProfile(models.Model):
    DEFAULT = 'default'
    CUSTOM = 'custom'
    GRAVATAR = 'gravatar'
    AVATAR_CHOICES = (
        (DEFAULT, _('Default')),
        (CUSTOM, _('Custom')),
        (GRAVATAR, 'Gravatar')
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wagtail_userprofile'
    )

    submitted_notifications = models.BooleanField(
        verbose_name=_('submitted notifications'),
        default=True,
        help_text=_("Receive notification when a page is submitted for moderation")
    )

    approved_notifications = models.BooleanField(
        verbose_name=_('approved notifications'),
        default=True,
        help_text=_("Receive notification when your page edit is approved")
    )

    rejected_notifications = models.BooleanField(
        verbose_name=_('rejected notifications'),
        default=True,
        help_text=_("Receive notification when your page edit is rejected")
    )

    preferred_language = models.CharField(
        verbose_name=_('preferred language'),
        max_length=10,
        help_text=_("Select language for the admin"),
        default=''
    )

    current_time_zone = models.CharField(
        verbose_name=_('current time zone'),
        max_length=40,
        help_text=_("Select your current time zone"),
        default=''
    )

    avatar_choice = models.CharField(
        verbose_name=_('Select profile picture type'),
        default=DEFAULT,
        choices=AVATAR_CHOICES,
        max_length=10
    )

    avatar = models.ImageField(
        verbose_name=_('Upload your custom avatar'),
        upload_to=upload_avatar_to,
        blank=True,
    )

    @classmethod
    def get_for_user(cls, user):
        return cls.objects.get_or_create(user=user)[0]

    def get_preferred_language(self):
        return self.preferred_language or settings.LANGUAGE_CODE

    def get_current_time_zone(self):
        return self.current_time_zone or settings.TIME_ZONE

    def __str__(self):
        return self.user.get_username()

    @cached_property
    def default_avatar(self):
        return static('wagtailadmin/images/default-user-avatar.png')

    class Meta:
        verbose_name = _('user profile')
