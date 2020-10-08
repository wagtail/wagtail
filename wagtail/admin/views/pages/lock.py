from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.http import is_safe_url
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from wagtail.admin import messages
from wagtail.admin.auth import permission_denied
from wagtail.core.models import Page


@require_POST
def lock(request, page_id):
    # Get the page
    page = get_object_or_404(Page, id=page_id).specific

    # Check permissions
    if not page.permissions_for_user(request.user).can_lock():
        return permission_denied(request)
    # Lock the page
    if not page.locked:
        page.locked = True
        page.locked_by = request.user
        page.locked_at = timezone.now()
        page.save(user=request.user, log_action='wagtail.lock')

    # Redirect
    redirect_to = request.POST.get('next', None)
    if redirect_to and is_safe_url(url=redirect_to, allowed_hosts={request.get_host()}):
        return redirect(redirect_to)
    else:
        return redirect('wagtailadmin_explore', page.get_parent().id)


@require_POST
def unlock(request, page_id):
    # Get the page
    page = get_object_or_404(Page, id=page_id).specific

    # Check permissions
    if not page.permissions_for_user(request.user).can_unlock():
        return permission_denied(request)

    # Unlock the page
    if page.locked:
        page.locked = False
        page.locked_by = None
        page.locked_at = None
        page.save(user=request.user, log_action='wagtail.unlock')

        messages.success(request, _("Page '{0}' is now unlocked.").format(page.get_admin_display_title()), extra_tags='unlock')

    # Redirect
    redirect_to = request.POST.get('next', None)
    if redirect_to and is_safe_url(url=redirect_to, allowed_hosts={request.get_host()}):
        return redirect(redirect_to)
    else:
        return redirect('wagtailadmin_explore', page.get_parent().id)
