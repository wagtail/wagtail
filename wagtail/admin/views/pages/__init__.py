from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext as _

from wagtail.admin import messages
from wagtail.admin.views.pages.utils import get_valid_next_url_from_request
from wagtail.core import hooks
from wagtail.core.models import Page, UserPagePermissionsProxy

from wagtail.admin.views.pages.copy import *  # noqa
from wagtail.admin.views.pages.create import *  # noqa
from wagtail.admin.views.pages.delete import *  # noqa
from wagtail.admin.views.pages.edit import *  # noqa
from wagtail.admin.views.pages.history import *  # noqa
from wagtail.admin.views.pages.listing import *  # noqa
from wagtail.admin.views.pages.lock import *  # noqa
from wagtail.admin.views.pages.moderation import *  # noqa
from wagtail.admin.views.pages.move import *  # noqa
from wagtail.admin.views.pages.preview import *  # noqa
from wagtail.admin.views.pages.revisions import *  # noqa
from wagtail.admin.views.pages.search import *  # noqa
from wagtail.admin.views.pages.usage import *  # noqa
from wagtail.admin.views.pages.workflow import *  # noqa


def unpublish(request, page_id):
    page = get_object_or_404(Page, id=page_id).specific

    user_perms = UserPagePermissionsProxy(request.user)
    if not user_perms.for_page(page).can_unpublish():
        raise PermissionDenied

    next_url = get_valid_next_url_from_request(request)

    if request.method == 'POST':
        include_descendants = request.POST.get("include_descendants", False)

        for fn in hooks.get_hooks('before_unpublish_page'):
            result = fn(request, page)
            if hasattr(result, 'status_code'):
                return result

        page.unpublish(user=request.user)

        if include_descendants:
            live_descendant_pages = page.get_descendants().live().specific()
            for live_descendant_page in live_descendant_pages:
                if user_perms.for_page(live_descendant_page).can_unpublish():
                    live_descendant_page.unpublish()

        for fn in hooks.get_hooks('after_unpublish_page'):
            result = fn(request, page)
            if hasattr(result, 'status_code'):
                return result

        messages.success(request, _("Page '{0}' unpublished.").format(page.get_admin_display_title()), buttons=[
            messages.button(reverse('wagtailadmin_pages:edit', args=(page.id,)), _('Edit'))
        ])

        if next_url:
            return redirect(next_url)
        return redirect('wagtailadmin_explore', page.get_parent().id)

    return TemplateResponse(request, 'wagtailadmin/pages/confirm_unpublish.html', {
        'page': page,
        'next': next_url,
        'live_descendant_count': page.get_descendants().live().count(),
    })


def set_page_position(request, page_to_move_id):
    page_to_move = get_object_or_404(Page, id=page_to_move_id)
    parent_page = page_to_move.get_parent()

    if not parent_page.permissions_for_user(request.user).can_reorder_children():
        raise PermissionDenied

    if request.method == 'POST':
        # Get position parameter
        position = request.GET.get('position', None)

        # Find page thats already in this position
        position_page = None
        if position is not None:
            try:
                position_page = parent_page.get_children()[int(position)]
            except IndexError:
                pass  # No page in this position

        # Move page

        # any invalid moves *should* be caught by the permission check above,
        # so don't bother to catch InvalidMoveToDescendant

        if position_page:
            # If the page has been moved to the right, insert it to the
            # right. If left, then left.
            old_position = list(parent_page.get_children()).index(page_to_move)
            if int(position) < old_position:
                page_to_move.move(position_page, pos='left')
            elif int(position) > old_position:
                page_to_move.move(position_page, pos='right')
        else:
            # Move page to end
            page_to_move.move(parent_page, pos='last-child')

    return HttpResponse('')
