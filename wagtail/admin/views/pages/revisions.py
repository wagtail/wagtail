from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from wagtail.admin import messages
from wagtail.admin.action_menu import PageActionMenu
from wagtail.admin.auth import user_has_any_page_permission, user_passes_test
from wagtail.admin.ui.side_panels import PageSidePanels
from wagtail.admin.views.generic.models import RevisionsCompareView
from wagtail.admin.views.pages.utils import get_valid_next_url_from_request
from wagtail.models import Page, UserPagePermissionsProxy


def revisions_index(request, page_id):
    return redirect("wagtailadmin_pages:history", page_id)


def revisions_revert(request, page_id, revision_id):
    page = get_object_or_404(Page, id=page_id).specific
    page_perms = page.permissions_for_user(request.user)
    if not page_perms.can_edit():
        raise PermissionDenied

    revision = get_object_or_404(page.revisions, id=revision_id)
    revision_page = revision.as_object()

    content_type = ContentType.objects.get_for_model(page)
    page_class = content_type.model_class()

    edit_handler = page_class.get_edit_handler()
    form_class = edit_handler.get_form_class()

    form = form_class(instance=revision_page)
    edit_handler = edit_handler.get_bound_panel(
        instance=revision_page, request=request, form=form
    )

    action_menu = PageActionMenu(request, view="revisions_revert", page=page)
    side_panels = PageSidePanels(
        request,
        page,
        preview_enabled=True,
        comments_enabled=form.show_comments_toggle,
    )

    user_avatar = render_to_string(
        "wagtailadmin/shared/user_avatar.html", {"user": revision.user}
    )

    messages.warning(
        request,
        mark_safe(
            _(
                "You are viewing a previous version of this page from <b>%(created_at)s</b> by %(user)s"
            )
            % {
                "created_at": revision.created_at.strftime("%d %b %Y %H:%M"),
                "user": user_avatar,
            }
        ),
    )

    return TemplateResponse(
        request,
        "wagtailadmin/pages/edit.html",
        {
            "page": page,
            "revision": revision,
            "is_revision": True,
            "content_type": content_type,
            "edit_handler": edit_handler,
            "errors_debug": None,
            "action_menu": action_menu,
            "side_panels": side_panels,
            "form": form,  # Used in unit tests
            "media": edit_handler.media
            + form.media
            + action_menu.media
            + side_panels.media,
        },
    )


@user_passes_test(user_has_any_page_permission)
def revisions_view(request, page_id, revision_id):
    page = get_object_or_404(Page, id=page_id).specific

    perms = page.permissions_for_user(request.user)
    if not (perms.can_publish() or perms.can_edit()):
        raise PermissionDenied

    revision = get_object_or_404(page.revisions, id=revision_id)
    revision_page = revision.as_object()

    try:
        preview_mode = page.default_preview_mode
    except IndexError:
        raise PermissionDenied

    return revision_page.make_preview_request(request, preview_mode)


class RevisionsCompare(RevisionsCompareView):
    history_label = gettext_lazy("Page history")
    edit_label = gettext_lazy("Edit this page")
    history_url_name = "wagtailadmin_pages:history"
    edit_url_name = "wagtailadmin_pages:edit"
    header_icon = "doc-empty-inverse"

    @method_decorator(user_passes_test(user_has_any_page_permission))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return get_object_or_404(Page, id=self.pk).specific

    def get_edit_handler(self):
        return self.object.get_edit_handler()

    def get_page_subtitle(self):
        return self.object.get_admin_display_title()


def revisions_unschedule(request, page_id, revision_id):
    page = get_object_or_404(Page, id=page_id).specific

    user_perms = UserPagePermissionsProxy(request.user)
    if not user_perms.for_page(page).can_unschedule():
        raise PermissionDenied

    revision = get_object_or_404(page.revisions, id=revision_id)

    next_url = get_valid_next_url_from_request(request)

    subtitle = _('revision {0} of "{1}"').format(
        revision.id, page.get_admin_display_title()
    )

    if request.method == "POST":
        revision.approved_go_live_at = None
        revision.save(user=request.user, update_fields=["approved_go_live_at"])

        messages.success(
            request,
            _('Version {0} of "{1}" unscheduled.').format(
                revision.id, page.get_admin_display_title()
            ),
            buttons=[
                messages.button(
                    reverse("wagtailadmin_pages:edit", args=(page.id,)), _("Edit")
                )
            ],
        )

        if next_url:
            return redirect(next_url)
        return redirect("wagtailadmin_pages:history", page.id)

    return TemplateResponse(
        request,
        "wagtailadmin/pages/revisions/confirm_unschedule.html",
        {"page": page, "revision": revision, "next": next_url, "subtitle": subtitle},
    )
