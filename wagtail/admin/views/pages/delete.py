from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import gettext as _

from wagtail.admin import messages
from wagtail.admin.views.pages.utils import get_valid_next_url_from_request
from wagtail.core import hooks
from wagtail.core.actions.delete_page import DeletePageAction
from wagtail.core.models import Page


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

        # The `construct_synced_page_tree_list` hook returns translation and
        # alias pages when the action is set to "delete"
        if getattr(settings, 'WAGTAIL_I18N_ENABLED', False):
            for fn in hooks.get_hooks("construct_synced_page_tree_list"):
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
            if getattr(settings, 'WAGTAIL_I18N_ENABLED', False):
                parent_page_translations = page.get_parent().get_translations()
                for _page in pages_to_delete:
                    if _page.get_parent() in parent_page_translations:
                        action = DeletePageAction(_page, user=request.user)
                        # Permission checks are done above, so skip them in execute.
                        action.execute(skip_permission_checks=True)

            messages.success(
                request, _("Page '{0}' deleted.").format(page.get_admin_display_title())
            )

            for fn in hooks.get_hooks("after_delete_page"):
                pages_to_delete.remove(page)
                for _page in pages_to_delete:
                    fn(request, _page)

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
            "translation_count": len(pages_to_delete),
            "translation_descendant_count": sum(
                [p.get_descendants().count() for p in pages_to_delete]
            ),
            "combined_subpages": page.get_descendant_count()
            + len(pages_to_delete),
        },
    )
