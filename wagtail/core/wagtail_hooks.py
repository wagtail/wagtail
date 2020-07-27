from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.auth.views import redirect_to_login
from django.urls import reverse
from django.utils.translation import ngettext

from wagtail.core import hooks
from wagtail.core.models import PageViewRestriction
from wagtail.core.rich_text.pages import PageLinkHandler


def require_wagtail_login(next):
    login_url = getattr(settings, 'WAGTAIL_FRONTEND_LOGIN_URL', reverse('wagtailcore_login'))
    return redirect_to_login(next, login_url)


@hooks.register('before_serve_page')
def check_view_restrictions(page, request, serve_args, serve_kwargs):
    """
    Check whether there are any view restrictions on this page which are
    not fulfilled by the given request object. If there are, return an
    HttpResponse that will notify the user of that restriction (and possibly
    include a password / login form that will allow them to proceed). If
    there are no such restrictions, return None
    """
    for restriction in page.get_view_restrictions():
        if not restriction.accept_request(request):
            if restriction.restriction_type == PageViewRestriction.PASSWORD:
                from wagtail.core.forms import PasswordViewRestrictionForm
                form = PasswordViewRestrictionForm(instance=restriction,
                                                   initial={'return_url': request.get_full_path()})
                action_url = reverse('wagtailcore_authenticate_with_password', args=[restriction.id, page.id])
                return page.serve_password_required_response(request, form, action_url)

            elif restriction.restriction_type in [PageViewRestriction.LOGIN, PageViewRestriction.GROUPS]:
                return require_wagtail_login(next=request.get_full_path())


@hooks.register('register_rich_text_features')
def register_core_features(features):
    features.default_features.append('hr')

    features.default_features.append('link')
    features.register_link_type(PageLinkHandler)

    features.default_features.append('bold')

    features.default_features.append('italic')

    features.default_features.extend(['h2', 'h3', 'h4'])

    features.default_features.append('ol')

    features.default_features.append('ul')


@hooks.register('register_permissions')
def register_collection_permissions():
    return Permission.objects.filter(
        content_type__app_label='wagtailcore',
        codename__in=['add_collection', 'change_collection', 'delete_collection']
    )


@hooks.register('register_permissions')
def register_workflow_permissions():
    return Permission.objects.filter(
        content_type__app_label='wagtailcore',
        codename__in=['add_workflow', 'change_workflow', 'delete_workflow']
    )


@hooks.register('register_permissions')
def register_task_permissions():
    return Permission.objects.filter(
        content_type__app_label='wagtailcore',
        codename__in=['add_task', 'change_task', 'delete_task']
    )


@hooks.register('describe_collection_contents')
def describe_collection_children(collection):
    descendant_count = collection.get_descendants().count()
    if descendant_count:
        url = reverse('wagtailadmin_collections:index')
        return {
            'count': descendant_count,
            'count_text': ngettext(
                "%(count)s descendant collection",
                "%(count)s descendant collections",
                descendant_count
            ) % {'count': descendant_count},
            'url': url,
        }
