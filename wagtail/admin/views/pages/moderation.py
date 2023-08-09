from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET

from wagtail.admin import messages
from wagtail.admin.mail import send_moderation_notification
from wagtail.models import Revision


def approve_moderation(request, revision_id):
    revision = get_object_or_404(Revision.page_revisions, id=revision_id)
    if not revision.content_object.permissions_for_user(request.user).can_publish():
        raise PermissionDenied

    if not revision.submitted_for_moderation:
        messages.error(
            request,
            _("The page '%(page_title)s' is not currently awaiting moderation.")
            % {
                "page_title": revision.content_object.specific_deferred.get_admin_display_title()
            },
        )
        return redirect("wagtailadmin_home")

    if request.method == "POST":
        revision.approve_moderation(user=request.user)

        message = _("Page '%(page_title)s' published.") % {
            "page_title": revision.content_object.specific_deferred.get_admin_display_title()
        }
        buttons = []
        if revision.content_object.url is not None:
            buttons.append(
                messages.button(
                    revision.content_object.url, _("View live"), new_window=False
                )
            )
        buttons.append(
            messages.button(
                reverse("wagtailadmin_pages:edit", args=(revision.content_object.id,)),
                _("Edit"),
            )
        )
        messages.success(request, message, buttons=buttons)

        if not send_moderation_notification(revision, "approved", request.user):
            messages.error(request, _("Failed to send approval notifications"))

    return redirect("wagtailadmin_home")


def reject_moderation(request, revision_id):
    revision = get_object_or_404(Revision.page_revisions, id=revision_id)
    if not revision.content_object.permissions_for_user(request.user).can_publish():
        raise PermissionDenied

    if not revision.submitted_for_moderation:
        messages.error(
            request,
            _("The page '%(page_title)s' is not currently awaiting moderation.")
            % {
                "page_title": revision.content_object.specific_deferred.get_admin_display_title()
            },
        )
        return redirect("wagtailadmin_home")

    if request.method == "POST":
        revision.reject_moderation(user=request.user)

        messages.success(
            request,
            _("Page '%(page_title)s' rejected for publication.")
            % {
                "page_title": revision.content_object.specific_deferred.get_admin_display_title()
            },
            buttons=[
                messages.button(
                    reverse(
                        "wagtailadmin_pages:edit", args=(revision.content_object.id,)
                    ),
                    _("Edit"),
                )
            ],
        )

        if not send_moderation_notification(revision, "rejected", request.user):
            messages.error(request, _("Failed to send rejection notifications"))

    return redirect("wagtailadmin_home")


@require_GET
def preview_for_moderation(request, revision_id):
    revision = get_object_or_404(Revision.page_revisions, id=revision_id)
    if not revision.content_object.permissions_for_user(request.user).can_publish():
        raise PermissionDenied

    if not revision.submitted_for_moderation:
        messages.error(
            request,
            _("The page '%(page_title)s' is not currently awaiting moderation.")
            % {
                "page_title": revision.content_object.specific_deferred.get_admin_display_title()
            },
        )
        return redirect("wagtailadmin_home")

    page = revision.as_object()

    try:
        preview_mode = page.default_preview_mode
    except IndexError:
        raise PermissionDenied

    return page.make_preview_request(
        request, preview_mode, extra_request_attrs={"revision_id": revision_id}
    )
