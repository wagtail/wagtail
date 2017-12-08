from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.urls import reverse

from wagtail.admin.rich_text.converters.editor_html import WhitelistRule
from wagtail.core import hooks
from wagtail.core.models import PageViewRestriction
from wagtail.core.rich_text.pages import PageLinkHandler, page_linktype_handler
from wagtail.core.whitelist import allow_without_attributes, attribute_rule, check_url


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
    features.register_converter_rule('editorhtml', 'hr', [
        WhitelistRule('hr', allow_without_attributes)
    ])

    features.default_features.append('link')
    features.register_converter_rule('editorhtml', 'link', [
        WhitelistRule('a', attribute_rule({'href': check_url}))
    ])
    features.register_link_type('page', page_linktype_handler)
    features.register_link_handler_rules('link', {'page': PageLinkHandler})

    features.default_features.append('bold')
    features.register_converter_rule('editorhtml', 'bold', [
        WhitelistRule('b', allow_without_attributes),
        WhitelistRule('strong', allow_without_attributes),
    ])

    features.default_features.append('italic')
    features.register_converter_rule('editorhtml', 'italic', [
        WhitelistRule('i', allow_without_attributes),
        WhitelistRule('em', allow_without_attributes),
    ])

    features.default_features.extend(['h2', 'h3', 'h4'])
    for element in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        features.register_converter_rule('editorhtml', element, [
            WhitelistRule(element, allow_without_attributes)
        ])

    features.default_features.append('ol')
    features.register_converter_rule('editorhtml', 'ol', [
        WhitelistRule('ol', allow_without_attributes),
        WhitelistRule('li', allow_without_attributes),
    ])

    features.default_features.append('ul')
    features.register_converter_rule('editorhtml', 'ul', [
        WhitelistRule('ul', allow_without_attributes),
        WhitelistRule('li', allow_without_attributes),
    ])
