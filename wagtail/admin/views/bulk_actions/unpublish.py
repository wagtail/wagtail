from urllib.parse import urlencode

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_list_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext as _

from wagtail.admin import messages
from wagtail.admin.views.pages.utils import get_valid_next_url_from_request
from wagtail.core import hooks
from wagtail.core.models import Page, UserPagePermissionsProxy


def unpublish(request, parent_page_id):
    next_url = get_valid_next_url_from_request(request)
    if not next_url:
        next_url = reverse('wagtailadmin_explore', args=[parent_page_id])

    page_ids = list(map(int, request.GET.getlist('id')))
    user_perms = UserPagePermissionsProxy(request.user)
    pages = []

    for page in get_list_or_404(Page, id__in=page_ids):
        page = page.specific
        if not user_perms.for_page(page).can_unpublish():
            raise PermissionDenied
        pages.append(page)
        page.unpublish

    if request.method == 'GET':
        _pages = []
        for page in pages:
            _pages.append({
                'page': page,
                'live_descendant_count': page.get_descendants().live().count(),
            })

        return TemplateResponse(request, 'wagtailadmin/pages/bulk_actions/confirm_bulk_unpublish.html', {
            'pages': _pages,
            'next': next_url,
            'submit_url': (
                reverse('wagtailadmin_bulk_unpublish', args=[parent_page_id])
                + '?' + urlencode([('id', page_id) for page_id in page_ids])
            ),
            'has_live_descendants': any(map(lambda x: x['live_descendant_count'] > 0, _pages)),
        })
    elif request.method == 'POST':
        num_parent_pages = 0
        include_descendants = request.POST.get("include_descendants", False)
        if include_descendants:
            num_child_pages = 0
        with transaction.atomic():
            for page in pages:
                for fn in hooks.get_hooks('before_unpublish_page'):
                    result = fn(request, page)
                    if hasattr(result, 'status_code'):
                        return result

                page.unpublish(user=request.user)
                num_parent_pages += 1

                if include_descendants:
                    for live_descendant_page in page.get_descendants().live().defer_streamfields().specific():
                        if user_perms.for_page(live_descendant_page).can_unpublish():
                            live_descendant_page.unpublish()
                            num_child_pages += 1

                for fn in hooks.get_hooks('after_unpublish_page'):
                    result = fn(request, page)
                    if hasattr(result, 'status_code'):
                        return result

        if include_descendants:
            messages.success(request, _(f'You have unpublished {num_parent_pages} pages including {num_child_pages} child pages.'))
        else:
            messages.success(request, _(f'You have unpublished {num_parent_pages} pages.'))
    return redirect(next_url)
