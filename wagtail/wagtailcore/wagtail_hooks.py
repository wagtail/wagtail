from __future__ import absolute_import, unicode_literals
from urllib.parse import unquote

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.views import redirect_to_login
from django.core.urlresolvers import reverse

from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.models import BaseViewRestriction


def require_wagtail_login(next):
    login_url = getattr(settings, 'WAGTAIL_FRONTEND_LOGIN_URL', reverse('wagtailcore_login'))
    return redirect_to_login(next, login_url)


@hooks.register('before_serve_page')
def check_page_view_restrictions(page, request, serve_args, serve_kwargs):
    """
    Check whether there are any view restrictions on this page which are
    not fulfilled by the given request object. If there are, return an
    HttpResponse that will notify the user of that restriction (and possibly
    include a password / login form that will allow them to proceed). If
    there are no such restrictions, return None
    """
    for restriction in page.get_view_restrictions():
        if not restriction.accept_request(request):
            if restriction.restriction_type == BaseViewRestriction.PASSWORD:
                from wagtail.wagtailcore.forms import PasswordBaseViewRestrictionForm
                form = PasswordBaseViewRestrictionForm(instance=restriction,
                                                       initial={'return_url': request.get_full_path()})
                action_url = reverse('wagtailcore_authenticate_with_password', args=['page', restriction.id, 0, page.id])
                return page.serve_password_required_response(request, form, action_url)

            elif restriction.restriction_type in [BaseViewRestriction.LOGIN, BaseViewRestriction.GROUPS]:
                return require_wagtail_login(next=request.get_full_path())


@hooks.register('before_serve_from_collection')
def check_collection_view_restrictions(collection, request, *serve_args, **serve_kwargs):
    """
    Check whether there are any view restrictions on the collection which are
    not fulfilled by the given request object. If there are, return an
    HttpResponse that will notify the user of that restriction (and possibly
    include a password / login form that will allow them to proceed). If
    there are no such restrictions, return None
    """
    obj = serve_kwargs.get('obj')
    obj_type = ContentType.objects.get_for_model(obj)
    for restriction in collection.get_view_restrictions():
        if not restriction.accept_request(request):
            if restriction.restriction_type == BaseViewRestriction.PASSWORD:
                from wagtail.wagtailcore.forms import PasswordBaseViewRestrictionForm
                form = PasswordBaseViewRestrictionForm(instance=restriction,
                                                       initial={'return_url': unquote(request.get_full_path())})
                action_url = reverse('wagtailcore_authenticate_with_password', args=['collection', restriction.id, obj_type.id, obj.id])
                return collection.serve_password_required_response(request, form, action_url)

            elif restriction.restriction_type in [BaseViewRestriction.LOGIN, BaseViewRestriction.GROUPS]:
                return require_wagtail_login(next=unquote(request.get_full_path()))
