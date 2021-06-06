from urllib.parse import urlencode

from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_list_or_404, get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from wagtail.admin import messages
from wagtail.admin.views.pages.utils import get_valid_next_url_from_request
from wagtail.core import hooks
from wagtail.core.models import Page


def move(request, parent_page_id, dest_page_id=None):
    next_url = get_valid_next_url_from_request(request)
    if not next_url:
        next_url = reverse('wagtailadmin_explore', args=[parent_page_id])

    page_ids = list(map(int, request.GET.getlist('id')))
    child_pages = set()
    if dest_page_id:
        viewed_page = get_object_or_404(Page, id=dest_page_id)
    else:
        viewed_page = Page.get_first_root_node()

    for _page in get_list_or_404(Page, id__in=page_ids):
        page_to_move = _page.specific
        page_perms = page_to_move.permissions_for_user(request.user)
        if not page_perms.can_move():
            raise PermissionDenied
        viewed_page.can_choose = page_perms.can_move_to(viewed_page)
        for target in viewed_page.get_children():
            target.can_choose = page_perms.can_move_to(target)

            target.can_descend = (
                not(target == page_to_move
                    or target.is_child_of(page_to_move))
                and target.get_children_count()
            )

            child_pages.add(target)

    child_pages = list(child_pages)
    paginator = Paginator(child_pages, per_page=50)
    child_pages = paginator.get_page(request.GET.get('p'))
    print(len(child_pages))

    if request.method == 'GET':
        args = [parent_page_id]
        if dest_page_id:
            args.append(dest_page_id)
        return TemplateResponse(request, 'wagtailadmin/pages/bulk_actions/bulk_move_choose_destination.html', {
            'num_pages': len(page_ids),
            'viewed_page': viewed_page,
            'child_pages': child_pages,
            'parent_page_id': parent_page_id,
            'page_ids': '?id=' + '&id='.join(request.GET.getlist('id')),
            'is_moving': True
        })


def move_confirm(request, parent_page_id, dest_page_id):
    next_url = get_valid_next_url_from_request(request)
    if not next_url:
        next_url = reverse('wagtailadmin_explore', args=[parent_page_id])

    destination = get_object_or_404(Page, id=dest_page_id).specific_deferred

    page_ids = list(map(int, request.GET.getlist('id')))
    pages_to_move = []
    for _page in get_list_or_404(Page, id__in=page_ids):
        page_to_move = _page.specific
        page_perms = page_to_move.permissions_for_user(request.user)
        if not page_perms.can_move():
            raise PermissionDenied
        if not page_perms.can_move_to(destination):
            raise PermissionDenied
        if not Page._slug_is_available(page_to_move.slug, destination, page=page_to_move):
            messages.error(
                request,
                _("The slug '{0}' is already in use at the selected parent page. Make sure the slug is unique and try again").format(page_to_move.slug)
            )
            return redirect('wagtailadmin_pages:move_choose_destination', page_to_move.id, dest_page_id)
        for fn in hooks.get_hooks('before_move_page'):
            result = fn(request, page_to_move, destination)
            if hasattr(result, 'status_code'):
                return result
        pages_to_move.append(page_to_move)

    if request.method == 'GET':
        return TemplateResponse(request, 'wagtailadmin/pages/bulk_actions/confirm_bulk_move.html', {
            'num_pages': len(page_ids),
            'pages_to_move': pages_to_move,
            'destination': destination,
            'submit_url': reverse('wagtailadmin_bulk_move_confirm', args=[parent_page_id, dest_page_id])
            + '?' + urlencode([('id', page_id) for page_id in page_ids]),
        })
    else:
        for page_to_move in pages_to_move:
            page_to_move.move(destination, pos='last-child', user=request.user)

        for fn in hooks.get_hooks('after_move_page'):
            result = fn(request, page_to_move)
            if hasattr(result, 'status_code'):
                return result
        messages.success(request, _(f"{len(page_ids)} pages moved."))
        return redirect(next_url)
