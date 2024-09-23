from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.utils.translation import gettext as _

from wagtail.admin.views.generic import lock
from wagtail.models import Page


class PageOperationViewMixin:
    model = Page
    pk_url_kwarg = "page_id"

    def get_object(self):
        return super().get_object().specific

    def get_success_url(self):
        if self.next_url:
            return self.next_url
        return reverse("wagtailadmin_explore", args=[self.object.get_parent().id])


class LockView(PageOperationViewMixin, lock.LockView):
    def perform_operation(self):
        if not self.object.permissions_for_user(self.request.user).can_lock():
            raise PermissionDenied
        return super().perform_operation()


class UnlockView(PageOperationViewMixin, lock.UnlockView):
    def perform_operation(self):
        if not self.object.permissions_for_user(self.request.user).can_unlock():
            raise PermissionDenied
        return super().perform_operation()

    def get_success_message(self):
        return _("Page '%(page_title)s' is now unlocked.") % {
            "page_title": self.object.get_admin_display_title()
        }
