from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import gettext as _

from wagtail.admin import messages
from wagtail.admin.views.pages.utils import get_valid_next_url_from_request
from wagtail.core import hooks
from wagtail.core.models import Page, PageLogEntry


def convert_alias(request, page_id):
    page = get_object_or_404(Page, id=page_id, alias_of_id__isnull=False).specific
    if not page.permissions_for_user(request.user).can_edit():
        raise PermissionDenied

    with transaction.atomic():
        for fn in hooks.get_hooks('before_convert_alias_page'):
            result = fn(request, page)
            if hasattr(result, 'status_code'):
                return result

        next_url = get_valid_next_url_from_request(request)

        if request.method == 'POST':
            page.alias_of_id = None
            page.save(update_fields=['alias_of_id'], clean=False)

            # Create an initial revision
            revision = page.save_revision(user=request.user, changed=False, clean=False)

            if page.live:
                page.live_revision = revision
                page.save(update_fields=['live_revision'], clean=False)

            # Log
            PageLogEntry.objects.log_action(
                instance=page,
                revision=revision,
                action='wagtail.convert_alias',
                user=request.user,
                data={
                    'page': {
                        'id': page.id,
                        'title': page.get_admin_display_title()
                    },
                },
            )

            messages.success(request, _("Page '{0}' has been converted into a regular page.").format(page.get_admin_display_title()))

            for fn in hooks.get_hooks('after_convert_alias_page'):
                result = fn(request, page)
                if hasattr(result, 'status_code'):
                    return result

            if next_url:
                return redirect(next_url)
            return redirect('wagtailadmin_pages:edit', page.id)

    return TemplateResponse(request, 'wagtailadmin/pages/confirm_convert_alias.html', {
        'page': page,
        'next': next_url,
    })
