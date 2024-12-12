from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from wagtail.admin import messages
from wagtail.admin.action_menu import PageActionMenu
from wagtail.admin.auth import user_has_any_page_permission, user_passes_test
from wagtail.admin.views.generic.models import (
    RevisionsCompareView,
    RevisionsUnscheduleView,
)
from wagtail.admin.views.generic.preview import PreviewRevision
from wagtail.admin.views.pages.edit import EditView
from wagtail.admin.views.pages.utils import GenericPageBreadcrumbsMixin
from wagtail.models import Page
from wagtail.utils.timestamps import render_timestamp


def revisions_index(request, page_id):
    return redirect("wagtailadmin_pages:history", page_id)


class RevisionsRevertView(EditView):
    revisions_revert_url_name = "wagtailadmin_pages:revisions_revert"

    def get_action_menu(self):
        return PageActionMenu(
            self.request,
            view="revisions_revert",
            is_revision=True,
            page=self.page,
            lock=self.lock,
            locked_for_user=self.locked_for_user,
        )

    def get(self, request, *args, **kwargs):
        self._add_warning_message()
        return super().get(request, *args, **kwargs)

    def _add_warning_message(self):
        messages.warning(self.request, self.get_warning_message())

    def get_object(self):
        return self.previous_revision.as_object()

    def get_revisions_revert_url(self):
        return reverse(
            self.revisions_revert_url_name,
            args=[self.page.pk, self.revision_id],
        )

    def get_warning_message(self):
        user_avatar = render_to_string(
            "wagtailadmin/shared/user_avatar.html",
            {"user": self.previous_revision.user},
        )

        return mark_safe(
            _(
                "You are viewing a previous version of this page from <b>%(created_at)s</b> by %(user)s"
            )
            % {
                "created_at": render_timestamp(self.previous_revision.created_at),
                "user": user_avatar,
            }
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action_url"] = self.get_revisions_revert_url()
        return context


@method_decorator(user_passes_test(user_has_any_page_permission), name="dispatch")
class RevisionsView(PreviewRevision):
    model = Page

    def setup(self, request, page_id, revision_id, *args, **kwargs):
        # Rename path kwargs from pk to page_id
        return super().setup(request, page_id, revision_id, *args, **kwargs)

    def get_object(self):
        page = get_object_or_404(Page, id=self.pk).specific

        perms = page.permissions_for_user(self.request.user)
        if not (perms.can_publish() or perms.can_edit()):
            raise PermissionDenied

        return page


class RevisionsCompare(GenericPageBreadcrumbsMixin, RevisionsCompareView):
    history_url_name = "wagtailadmin_pages:history"
    edit_url_name = "wagtailadmin_pages:edit"
    header_icon = "doc-empty-inverse"
    breadcrumbs_items_to_take = 2

    @method_decorator(user_passes_test(user_has_any_page_permission))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return get_object_or_404(Page, id=self.pk).specific

    def get_edit_handler(self):
        return self.object.get_edit_handler()

    def get_page_subtitle(self):
        return self.object.get_admin_display_title()


class RevisionsUnschedule(RevisionsUnscheduleView):
    model = Page
    edit_url_name = "wagtailadmin_pages:edit"
    history_url_name = "wagtailadmin_pages:history"
    revisions_unschedule_url_name = "wagtailadmin_pages:revisions_unschedule"
    header_icon = "doc-empty-inverse"

    def setup(self, request, page_id, revision_id, *args, **kwargs):
        # Rename path kwargs from pk to page_id
        return super().setup(request, page_id, revision_id, *args, **kwargs)

    def get_object(self, queryset=None):
        page = get_object_or_404(Page, id=self.pk).specific

        if not page.permissions_for_user(self.request.user).can_unschedule():
            raise PermissionDenied
        return page

    def get_object_display_title(self):
        return self.object.get_admin_display_title()
