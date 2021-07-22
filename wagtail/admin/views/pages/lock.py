from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from wagtail.admin import messages
from wagtail.core.models import Page


@require_POST
def lock(request, page_id):
    # Get the page
    page = get_object_or_404(Page, id=page_id).specific

    # Check permissions
    if not page.permissions_for_user(request.user).can_lock():
        raise PermissionDenied
    # Lock the page
    if not page.locked:
        page.locked = True
        page.locked_by = request.user
        page.locked_at = timezone.now()
        page.save(user=request.user, log_action='wagtail.lock')

    # Redirect
    redirect_to = request.POST.get('next', None)
    if redirect_to and url_has_allowed_host_and_scheme(url=redirect_to, allowed_hosts={request.get_host()}):
        return redirect(redirect_to)
    else:
        return redirect('wagtailadmin_explore', page.get_parent().id)


@require_POST
def unlock(request, page_id):
    # Get the page
    page = get_object_or_404(Page, id=page_id).specific

    # Check permissions
    if not page.permissions_for_user(request.user).can_unlock():
        raise PermissionDenied

    # Unlock the page
    if page.locked:
        page.locked = False
        page.locked_by = None
        page.locked_at = None
        page.save(user=request.user, log_action='wagtail.unlock')

        messages.success(request, _("Page '{0}' is now unlocked.").format(page.get_admin_display_title()), extra_tags='unlock')

    # Redirect
    redirect_to = request.POST.get('next', None)
    if redirect_to and url_has_allowed_host_and_scheme(url=redirect_to, allowed_hosts={request.get_host()}):
        return redirect(redirect_to)
    else:
        return redirect('wagtailadmin_explore', page.get_parent().id)
