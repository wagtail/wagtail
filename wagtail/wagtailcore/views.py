from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect

from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.forms import PasswordPageViewRestrictionForm
from wagtail.wagtailcore.models import Page, PageViewRestriction


def serve(request, path):
    # we need a valid Site object corresponding to this request (set in wagtail.wagtailcore.middleware.SiteMiddleware)
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
    Handle a submission of PasswordPageViewRestrictionForm to grant view access over a
    subtree that is protected by a PageViewRestriction
    """
    restriction = get_object_or_404(PageViewRestriction, id=page_view_restriction_id)
    page = get_object_or_404(Page, id=page_id).specific

    if request.method == 'POST':
        form = PasswordPageViewRestrictionForm(request.POST, instance=restriction)
        if form.is_valid():
            has_existing_session = (settings.SESSION_COOKIE_NAME in request.COOKIES)
            passed_restrictions = request.session.setdefault('passed_page_view_restrictions', [])
            if restriction.id not in passed_restrictions:
                passed_restrictions.append(restriction.id)
                request.session['passed_page_view_restrictions'] = passed_restrictions
            if not has_existing_session:
                # if this is a session we've created, set it to expire at the end
                # of the browser session
                request.session.set_expiry(0)

            return redirect(form.cleaned_data['return_url'])
    else:
        form = PasswordPageViewRestrictionForm(instance=restriction)

    action_url = reverse('wagtailcore_authenticate_with_password', args=[restriction.id, page.id])
    return page.serve_password_required_response(request, form, action_url)
