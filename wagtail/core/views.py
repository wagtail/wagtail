from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from wagtail.core import hooks
from wagtail.core.forms import PasswordViewRestrictionForm
from wagtail.core.models import Page, PageViewRestriction


def serve(request, path):
    # we need a valid Site object corresponding to this request (set in wagtail.core.middleware.SiteMiddleware)
    # in order to proceed
    if not request.site:
        raise Http404

    path_components = [component for component in path.split('/') if component]
    page, args, kwargs = request.site.root_page.specific.route(request, path_components)

    for fn in hooks.get_hooks('before_serve_page'):
        result = fn(page, request, args, kwargs)
        if isinstance(result, HttpResponse):
            return result

    return page.serve(request, *args, **kwargs)


def authenticate_with_password(request, page_view_restriction_id, page_id):
    """
    Handle a submission of PasswordViewRestrictionForm to grant view access over a
    subtree that is protected by a PageViewRestriction
    """
    restriction = get_object_or_404(PageViewRestriction, id=page_view_restriction_id)
    page = get_object_or_404(Page, id=page_id).specific

    if request.method == 'POST':
        form = PasswordViewRestrictionForm(request.POST, instance=restriction)
        if form.is_valid():
            restriction.mark_as_passed(request)

            return redirect(form.cleaned_data['return_url'])
    else:
        form = PasswordViewRestrictionForm(instance=restriction)

    action_url = reverse('wagtailcore_authenticate_with_password', args=[restriction.id, page.id])
    return page.serve_password_required_response(request, form, action_url)
