import sys

from django.conf import settings

from wagtail.admin.navigation import get_explorable_root_page
from wagtail.utils.deprecation import MovedDefinitionHandler, RemovedInWagtail29Warning


def get_site_for_user(user):
    root_page = get_explorable_root_page(user)
    if root_page:
        root_site = root_page.get_site()
    else:
        root_site = None
    real_site_name = None
    if root_site:
        real_site_name = root_site.site_name if root_site.site_name else root_site.hostname
    return {
        'root_page': root_page,
        'root_site': root_site,
        'site_name': real_site_name if real_site_name else settings.WAGTAIL_SITE_NAME,
    }


MOVED_DEFINITIONS = {
    'WAGTAILADMIN_PROVIDED_LANGUAGES': 'wagtail.admin.locale',
    'get_js_translation_strings': 'wagtail.admin.locale',
    'get_available_admin_languages': 'wagtail.admin.locale',
    'get_available_admin_time_zones': 'wagtail.admin.locale',

    'get_object_usage': 'wagtail.admin.models',
    'popular_tags_for_model': 'wagtail.admin.models',

    'users_with_page_permission': 'wagtail.admin.auth',
    'permission_denied': 'wagtail.admin.auth',
    'user_passes_test': 'wagtail.admin.auth',
    'permission_required': 'wagtail.admin.auth',
    'any_permission_required': 'wagtail.admin.auth',
    'PermissionPolicyChecker': 'wagtail.admin.auth',
    'user_has_any_page_permission': 'wagtail.admin.auth',

    'send_mail': 'wagtail.admin.mail',
    'send_notification': 'wagtail.admin.mail',
}

sys.modules[__name__] = MovedDefinitionHandler(sys.modules[__name__], MOVED_DEFINITIONS, RemovedInWagtail29Warning)
