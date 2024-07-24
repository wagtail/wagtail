from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import gettext as _

from wagtail import hooks
from wagtail.actions.convert_alias import ConvertAliasPageAction
from wagtail.admin import messages
from wagtail.admin.utils import get_valid_next_url_from_request
from wagtail.models import Page


def convert_alias(request, page_id):
    page = get_object_or_404(Page, id=page_id, alias_of_id__isnull=False).specific
    if not page.permissions_for_user(request.user).can_edit():
        raise PermissionDenied

    with transaction.atomic():
        for fn in hooks.get_hooks("before_convert_alias_page"):
            result = fn(request, page)
            if hasattr(result, "status_code"):
                return result

        next_url = get_valid_next_url_from_request(request)

        if request.method == "POST":
            action = ConvertAliasPageAction(page, user=request.user)
            action.execute(skip_permission_checks=True)

            messages.success(
                request,
                _("Page '%(page_title)s' has been converted into an ordinary page.")
                % {"page_title": page.get_admin_display_title()},
            )

            for fn in hooks.get_hooks("after_convert_alias_page"):
                result = fn(request, page)
                if hasattr(result, "status_code"):
                    return result

            if next_url:
                return redirect(next_url)
            return redirect("wagtailadmin_pages:edit", page.id)

    return TemplateResponse(
        request,
        "wagtailadmin/pages/confirm_convert_alias.html",
        {
            "page": page,
            "next": next_url,
        },
    )
