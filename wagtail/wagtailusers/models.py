from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


@python_2_unicode_compatible
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

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

    @classmethod
    def get_for_user(cls, user):
        return cls.objects.get_or_create(user=user)[0]

    def __str__(self):
        return self.user.get_username()

    class Meta:
        verbose_name = _('user profile')
