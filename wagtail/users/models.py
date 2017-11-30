from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _


class UserProfile(models.Model):
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

    @classmethod
    def get_for_user(cls, user):
        return cls.objects.get_or_create(user=user)[0]

    def get_preferred_language(self):
        return self.preferred_language or settings.LANGUAGE_CODE

    def __str__(self):
        return self.user.get_username()

    class Meta:
        verbose_name = _('user profile')
