import warnings

from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.core.urlresolvers import reverse

from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.models import Page, PageViewRestriction
from wagtail.wagtailcore.forms import PasswordPageViewRestrictionForm


def serve(request, path):
    # we need a valid Site object corresponding to this request (set in wagtail.wagtailcore.middleware.SiteMiddleware)
    # in order to proceed
    if not request.site:
        raise Http404

    path_components = [component for component in path.split('/') if component]
    page = request.site.root_page.specific.route(request, path_components)
    if isinstance(page, HttpResponse):
        warnings.warn(
            "Page.route should return a Page, not an HttpResponse",
            DeprecationWarning
        )
        return page

    for fn in hooks.get_hooks('before_serve_page'):
        result = fn(page, request)
        if isinstance(result, HttpResponse):
            return result

    return page.serve(request)


def authenticate_with_password(request, page_view_restriction_id, page_id):
    """
    Handle a submission of PasswordPageViewRestrictionForm to grant view access over a
    subtree that is protected by a PageViewRestriction
    """
    restriction = get_object_or_404(PageViewRestriction, id=page_view_restriction_id)
    page = get_object_or_404(Page, id=page_id).specific

    if request.POST:
        form = PasswordPageViewRestrictionForm(request.POST, instance=restriction)
        if form.is_valid():
            # TODO: record 'has authenticated against this page view restriction' flag in the session
            return redirect(form.cleaned_data['return_url'])
    else:
        form = PasswordPageViewRestrictionForm(instance=restriction)

    action_url = reverse('wagtailcore_authenticate_with_password', args=[restriction.id, page.id])
    return page.serve_password_required_response(request, form, action_url)
