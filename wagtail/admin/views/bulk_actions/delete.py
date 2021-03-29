from urllib.parse import urlencode

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, get_list_or_404
from django.db import transaction
from django.urls import reverse
from django.template.response import TemplateResponse
from django.utils.translation import gettext as _

from wagtail.admin import messages
from wagtail.admin.views.pages.utils import get_valid_next_url_from_request
from wagtail.core import hooks
from wagtail.core.models import Page


def delete(request, parent_page_id):
    next_url = get_valid_next_url_from_request(request)
    if not next_url:
        next_url = reverse('wagtailadmin_explore', args=[parent_page_id])
    
    page_ids = list(map(int, request.GET.getlist('id')))
    pages = []

    for page in get_list_or_404(Page, id__in=page_ids):
        page = page.specific
        if not page.permissions_for_user(request.user).can_delete():
            raise PermissionDenied
        pages.append(page)
    
    if request.method == 'GET':
        _pages = []
        for page in pages:
            _pages.append({
                'page': page,
                'descendant_count': page.get_descendant_count(),
            })

        return TemplateResponse(request, 'wagtailadmin/pages/bulk_actions/confirm_bulk_delete.html', {
            'pages': _pages,
            'next': next_url,
            'submit_url': (
                reverse('wagtailadmin_bulk_delete', args=[parent_page_id])
                + '?' + urlencode([('id', page_id) for page_id in page_ids])
            ),
        })
    elif request.method == 'POST':
        num_parent_pages = 0
        num_child_pages = 0
        with transaction.atomic():
            for page in pages:
                num_parent_pages += 1
                num_child_pages += page.get_descendant_count()
                for fn in hooks.get_hooks('before_delete_page'):
                    result = fn(request, page)
                    if hasattr(result, 'status_code'):
                        return result
                page.delete(user=request.user)

                for fn in hooks.get_hooks('after_delete_page'):
                    result = fn(request, page)
                    if hasattr(result, 'status_code'):
                        return result

        messages.success(request, _(f'You have successfully deleted {num_parent_pages} pages including '
                                        '{num_child_pages} child pages.'))
    return redirect(next_url)
