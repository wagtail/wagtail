from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext as _

from wagtail import hooks
from wagtail.actions.move_page import MovePageAction
from wagtail.admin import messages
from wagtail.models import Page


def move_choose_destination(request, page_to_move_id, viewed_page_id=None):
    page_to_move = get_object_or_404(Page, id=page_to_move_id)
    page_perms = page_to_move.permissions_for_user(request.user)
    if not page_perms.can_move():
        raise PermissionDenied

    if viewed_page_id:
        viewed_page = get_object_or_404(Page, id=viewed_page_id)
    else:
        viewed_page = page_to_move.get_parent()

    viewed_page.can_choose = page_perms.can_move_to(viewed_page)

    child_pages = []
    for target in viewed_page.get_children():
        # can't move the page into itself or its descendants
        target.can_choose = page_perms.can_move_to(target)

        target.can_descend = (
            not (target == page_to_move or target.is_child_of(page_to_move))
            and target.get_children_count()
        )

        child_pages.append(target)

    # Pagination
    paginator = Paginator(child_pages, per_page=50)
    child_pages = paginator.get_page(request.GET.get("p"))

    return TemplateResponse(
        request,
        "wagtailadmin/pages/move_choose_destination.html",
        {
            "page_to_move": page_to_move,
            "viewed_page": viewed_page,
            "child_pages": child_pages,
        },
    )


def move_confirm(request, page_to_move_id, destination_id):
    page_to_move = get_object_or_404(Page, id=page_to_move_id).specific
    # Needs .specific_deferred because the .get_admin_display_title method is called in template
    destination = get_object_or_404(Page, id=destination_id).specific_deferred

    if not Page._slug_is_available(page_to_move.slug, destination, page=page_to_move):
        messages.error(
            request,
            _(
                "The slug '{0}' is already in use at the selected parent page. Make sure the slug is unique and try again"
            ).format(page_to_move.slug),
        )
        return redirect(
            "wagtailadmin_pages:move_choose_destination",
            page_to_move.id,
            destination.id,
        )

    for fn in hooks.get_hooks("before_move_page"):
        result = fn(request, page_to_move, destination)
        if hasattr(result, "status_code"):
            return result

    if request.method == "POST":
        # any invalid moves *should* be caught by the permission check in the action class,
        # so don't bother to catch InvalidMoveToDescendant
        action = MovePageAction(
            page_to_move, destination, pos="last-child", user=request.user
        )
        action.execute()

        messages.success(
            request,
            _("Page '{0}' moved.").format(page_to_move.get_admin_display_title()),
            buttons=[
                messages.button(
                    reverse("wagtailadmin_pages:edit", args=(page_to_move.id,)),
                    _("Edit"),
                )
            ],
        )

        for fn in hooks.get_hooks("after_move_page"):
            result = fn(request, page_to_move)
            if hasattr(result, "status_code"):
                return result

        return redirect("wagtailadmin_explore", destination.id)

    return TemplateResponse(
        request,
        "wagtailadmin/pages/confirm_move.html",
        {
            "page_to_move": page_to_move,
            "destination": destination,
        },
    )
