from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _


User = get_user_model()


class UserProfile(models.Model):
    user = models.OneToOneField(User)

    submitted_notifications = models.BooleanField(
            default=True,
            help_text=_("Receive notification when a page is submitted for moderation")
            )

    approved_notifications = models.BooleanField(
            default=True,
            help_text=_("Receive notification when your page edit is approved")
            )

    rejected_notifications = models.BooleanField(
            default=True,
            help_text=_("Receive notification when your page edit is rejected")
            )

    @classmethod
    def get_for_user(cls, user):
        return cls.objects.get_or_create(user=user)[0]

    def __unicode__(self):
        return self.user.username
