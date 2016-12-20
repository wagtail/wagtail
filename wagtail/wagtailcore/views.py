from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect

from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.forms import PasswordBaseViewRestrictionForm
from wagtail.wagtailcore.models import (Collection, CollectionViewRestriction,
                                        Page, PageViewRestriction)


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


def authenticate_with_password(request, restriction_type, view_restriction_id, obj_type, obj_id):
    """
    Handle a submission of PasswordBaseViewRestrictionForm to grant view access over a
    subtree that is protected by a BaseViewRestriction
    """
    if restriction_type == 'page':
        restriction = get_object_or_404(PageViewRestriction, id=view_restriction_id)
        obj = get_object_or_404(Page, id=obj_id).specific
    elif restriction_type == 'collection':
        restriction = get_object_or_404(CollectionViewRestriction, id=view_restriction_id)
        klass = ContentType.objects.get_for_id(obj_type).model_class()
        obj = get_object_or_404(klass, id=obj_id)
    else:
        raise Exception('Unknown restriction type')

    if request.method == 'POST':
        form = PasswordBaseViewRestrictionForm(request.POST, instance=restriction)
        if form.is_valid():
            has_existing_session = (settings.SESSION_COOKIE_NAME in request.COOKIES)
            passed_restrictions = request.session.setdefault('passed_view_restrictions', [])
            if restriction.id not in passed_restrictions:
                passed_restrictions.append(restriction.id)
                request.session['passed_view_restrictions'] = passed_restrictions
            if not has_existing_session:
                # if this is a session we've created, set it to expire at the end
                # of the browser session
                request.session.set_expiry(0)

            return redirect(form.cleaned_data['return_url'])
    else:
        form = PasswordBaseViewRestrictionForm(instance=restriction)

    action_url = reverse('wagtailcore_authenticate_with_password', args=[restriction_type, restriction.id, obj_type, obj.id])
    if restriction_type == 'page':
        return obj.serve_password_required_response(request, form, action_url)
    elif restriction_type == 'collection':
        return obj.collection.serve_password_required_response(request, form, action_url)
