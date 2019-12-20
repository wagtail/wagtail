import sys

from wagtail.utils.deprecation import MovedDefinitionHandler, RemovedInWagtail29Warning


MOVED_DEFINITIONS = {
    'WAGTAILADMIN_PROVIDED_LANGUAGES': 'wagtail.admin.localization',
    'get_js_translation_strings': 'wagtail.admin.localization',
    'get_available_admin_languages': 'wagtail.admin.localization',
    'get_available_admin_time_zones': 'wagtail.admin.localization',

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

    'get_site_for_user': 'wagtail.admin.navigation',
}

sys.modules[__name__] = MovedDefinitionHandler(sys.modules[__name__], MOVED_DEFINITIONS, RemovedInWagtail29Warning)
