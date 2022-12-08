from django.utils import timezone
from django.utils.text import capfirst
from django.utils.translation import gettext as _

from wagtail.admin.utils import get_latest_str
from wagtail.admin.views.generic.base import BaseOperationView
from wagtail.log_actions import log


class LockView(BaseOperationView):
    success_message_extra_tags = "lock"

    def perform_operation(self):
        if self.object.locked:
            return
        self.object.locked = True
        self.object.locked_by = self.request.user
        self.object.locked_at = timezone.now()
        self.object.save(update_fields=["locked", "locked_by", "locked_at"])
        log(instance=self.object, action="wagtail.lock", user=self.request.user)


class UnlockView(BaseOperationView):
    success_message_extra_tags = "unlock"

    def perform_operation(self):
        if not self.object.locked:
            return
        self.object.locked = False
        self.object.locked_by = None
        self.object.locked_at = None
        self.object.save(update_fields=["locked", "locked_by", "locked_at"])
        log(instance=self.object, action="wagtail.unlock", user=self.request.user)

    def get_success_message(self):
        return capfirst(
            _("%(model_name)s '%(title)s' is now unlocked.")
            % {
                "model_name": self.model._meta.verbose_name,
                "title": get_latest_str(self.object),
            }
        )
