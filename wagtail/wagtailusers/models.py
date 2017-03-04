from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from wagtail.wagtailusers.utils import get_gravatar_url


def upload_avatar_to(instance, filename):
    return "avatar_images/avatar_{}_{}".format(instance.id, filename)


@python_2_unicode_compatible
class UserProfile(models.Model):
    DEFAULT = 'Default'
    CUSTOM = 'Custom'
    GRAVATAR = 'Gravatar'
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

    avatar_choice = models.CharField(
        verbose_name=_('Select avatar backend'),
        default=GRAVATAR,
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

    def __str__(self):
        return self.user.get_username()

    def get_avatar_url(self, size=50):
        default_avatar = static('wagtailadmin/images/default-user-avatar.svg')

        if self.avatar_choice == self.DEFAULT:
            return default_avatar
        elif self.avatar_choice == self.CUSTOM:
            try:
                return self.avatar.url
            except ValueError:
                return default_avatar
        else:
            if self.user.email:
                return get_gravatar_url(self.user.email, default=None, size=50)
            else:
                return default_avatar

    class Meta:
        verbose_name = _('user profile')
