from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext as _

from wagtail import hooks
from wagtail.actions.move_page import MovePageAction
from wagtail.admin import messages
from wagtail.admin.forms.pages import MoveForm
from wagtail.models import Page


def move_choose_destination(request, page_to_move_id):
    page_to_move = get_object_or_404(Page, id=page_to_move_id)
    page_perms = page_to_move.permissions_for_user(request.user)
    if not page_perms.can_move():
        raise PermissionDenied

    target_parent_models = set(page_to_move.specific_class.allowed_parent_page_models())

    move_form = MoveForm(
        request.POST or None,
        page_to_move=page_to_move,
        target_parent_models=target_parent_models,
    )

    if request.method == "POST":
        if move_form.is_valid():
            # Receive the new parent page (this should never be empty)
            if move_form.cleaned_data["new_parent_page"]:
                new_parent_page = move_form.cleaned_data["new_parent_page"]
                return redirect(
                    "wagtailadmin_pages:move_confirm",
                    page_to_move.id,
                    new_parent_page.id,
                )

    return TemplateResponse(
        request,
        "wagtailadmin/pages/move_choose_destination.html",
        {
            "page_to_move": page_to_move,
            "move_form": move_form,
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
                "The slug '%(page_slug)s' is already in use at the selected parent page. Make sure the slug is unique and try again"
            )
            % {"page_slug": page_to_move.slug},
        )
        return redirect(
            "wagtailadmin_pages:move",
            page_to_move.id,
        )

    for fn in hooks.get_hooks("before_move_page"):
        result = fn(request, page_to_move, destination)
        if hasattr(result, "status_code"):
            return result

    pages_to_move = {page_to_move}

    # The `construct_translated_pages_to_cascade_actions` hook returns translation and
    # alias pages when the action is set to "move"
    if getattr(settings, "WAGTAIL_I18N_ENABLED", False):
        for fn in hooks.get_hooks("construct_translated_pages_to_cascade_actions"):
            fn_pages = fn([page_to_move], "move")
            if fn_pages and isinstance(fn_pages, dict):
                for additional_pages in fn_pages.values():
                    pages_to_move.update(additional_pages)

    pages_to_move = list(pages_to_move)

    if request.method == "POST":
        # any invalid moves *should* be caught by the permission check in the action
        # class, so don't bother to catch InvalidMoveToDescendant
        action = MovePageAction(
            page_to_move, destination, pos="last-child", user=request.user
        )
        action.execute()

        if getattr(settings, "WAGTAIL_I18N_ENABLED", False):
            # Move translation and alias pages if they have the same parent page.
            parent_page_translations = page_to_move.get_parent().get_translations()
            for translation in pages_to_move:
                if translation.get_parent() in parent_page_translations:
                    # Move the translated or alias page to it's translated or
                    # alias "destination" page.
                    action = MovePageAction(
                        translation,
                        destination.get_translation(translation.locale),
                        pos="last-child",
                        user=request.user,
                    )
                    action.execute()

        messages.success(
            request,
            _("Page '%(page_title)s' moved.")
            % {"page_title": page_to_move.get_admin_display_title()},
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
            "translations_to_move_count": len(
                [
                    translation.id
                    for translation in pages_to_move
                    if not translation.alias_of_id and translation.id != page_to_move.id
                ]
            ),
        },
    )
