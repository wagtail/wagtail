from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import gettext as _

from wagtail import hooks
from wagtail.actions.delete_page import DeletePageAction
from wagtail.admin import messages
from wagtail.admin.views.pages.utils import get_valid_next_url_from_request
from wagtail.models import Page


def delete(request, page_id):
    page = get_object_or_404(Page, id=page_id).specific
    if not page.permissions_for_user(request.user).can_delete():
        raise PermissionDenied

    with transaction.atomic():
        for fn in hooks.get_hooks("before_delete_page"):
            result = fn(request, page)
            if hasattr(result, "status_code"):
                return result

        next_url = get_valid_next_url_from_request(request)

        pages_to_delete = {page}

        # The `construct_translated_pages_to_cascade_actions` hook returns translation and
        # alias pages when the action is set to "delete"
        if getattr(settings, "WAGTAIL_I18N_ENABLED", False):
            for fn in hooks.get_hooks("construct_translated_pages_to_cascade_actions"):
                fn_pages = fn([page], "delete")
                if fn_pages and isinstance(fn_pages, dict):
                    for additional_pages in fn_pages.values():
                        pages_to_delete.update(additional_pages)

        pages_to_delete = list(pages_to_delete)

        if request.method == "POST":
            parent_id = page.get_parent().id
            # Delete the source page.
            action = DeletePageAction(page, user=request.user)
            # Permission checks are done above, so skip them in execute.
            action.execute(skip_permission_checks=True)

            # Delete translation and alias pages if they have the same parent page.
            if getattr(settings, "WAGTAIL_I18N_ENABLED", False):
                parent_page_translations = page.get_parent().get_translations()
                for page_or_alias in pages_to_delete:
                    if page_or_alias.get_parent() in parent_page_translations:
                        action = DeletePageAction(page_or_alias, user=request.user)
                        # Permission checks are done above, so skip them in execute.
                        action.execute(skip_permission_checks=True)

            messages.success(
                request, _("Page '{0}' deleted.").format(page.get_admin_display_title())
            )

            for fn in hooks.get_hooks("after_delete_page"):
                result = fn(request, page)
                if hasattr(result, "status_code"):
                    return result

            if next_url:
                return redirect(next_url)
            return redirect("wagtailadmin_explore", parent_id)

    return TemplateResponse(
        request,
        "wagtailadmin/pages/confirm_delete.html",
        {
            "page": page,
            "descendant_count": page.get_descendant_count(),
            "next": next_url,
            # note that while pages_to_delete may contain a mix of translated pages
            # and aliases, we count the "translations" only, as aliases are similar
            # to symlinks, so they should just follow the source
            "translation_count": len(
                [
                    translation.id
                    for translation in pages_to_delete
                    if not translation.alias_of_id and translation.id != page.id
                ]
            ),
            "translation_descendant_count": sum(
                [
                    translation.get_descendants().filter(alias_of__isnull=True).count()
                    for translation in pages_to_delete
                ]
            ),
        },
    )
