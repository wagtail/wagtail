from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET

from wagtail.admin import messages
from wagtail.admin.mail import send_moderation_notification
from wagtail.models import PageRevision


def approve_moderation(request, revision_id):
    revision = get_object_or_404(PageRevision, id=revision_id)
    if not revision.page.permissions_for_user(request.user).can_publish():
        raise PermissionDenied

    if not revision.submitted_for_moderation:
        messages.error(
            request,
            _("The page '{0}' is not currently awaiting moderation.").format(
                revision.page.specific_deferred.get_admin_display_title()
            ),
        )
        return redirect("wagtailadmin_home")

    if request.method == "POST":
        revision.approve_moderation(user=request.user)

        message = _("Page '{0}' published.").format(
            revision.page.specific_deferred.get_admin_display_title()
        )
        buttons = []
        if revision.page.url is not None:
            buttons.append(
                messages.button(revision.page.url, _("View live"), new_window=False)
            )
        buttons.append(
            messages.button(
                reverse("wagtailadmin_pages:edit", args=(revision.page.id,)), _("Edit")
            )
        )
        messages.success(request, message, buttons=buttons)

        if not send_moderation_notification(revision, "approved", request.user):
            messages.error(request, _("Failed to send approval notifications"))

    return redirect("wagtailadmin_home")


def reject_moderation(request, revision_id):
    revision = get_object_or_404(PageRevision, id=revision_id)
    if not revision.page.permissions_for_user(request.user).can_publish():
        raise PermissionDenied

    if not revision.submitted_for_moderation:
        messages.error(
            request,
            _("The page '{0}' is not currently awaiting moderation.").format(
                revision.page.specific_deferred.get_admin_display_title()
            ),
        )
        return redirect("wagtailadmin_home")

    if request.method == "POST":
        revision.reject_moderation(user=request.user)

        messages.success(
            request,
            _("Page '{0}' rejected for publication.").format(
                revision.page.specific_deferred.get_admin_display_title()
            ),
            buttons=[
                messages.button(
                    reverse("wagtailadmin_pages:edit", args=(revision.page.id,)),
                    _("Edit"),
                )
            ],
        )

        if not send_moderation_notification(revision, "rejected", request.user):
            messages.error(request, _("Failed to send rejection notifications"))

    return redirect("wagtailadmin_home")


@require_GET
def preview_for_moderation(request, revision_id):
    revision = get_object_or_404(PageRevision, id=revision_id)
    if not revision.page.permissions_for_user(request.user).can_publish():
        raise PermissionDenied

    if not revision.submitted_for_moderation:
        messages.error(
            request,
            _("The page '{0}' is not currently awaiting moderation.").format(
                revision.page.specific_deferred.get_admin_display_title()
            ),
        )
        return redirect("wagtailadmin_home")

    page = revision.as_page_object()

    try:
        preview_mode = page.default_preview_mode
    except IndexError:
        raise PermissionDenied

    return page.make_preview_request(
        request, preview_mode, extra_request_attrs={"revision_id": revision_id}
    )
