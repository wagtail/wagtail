import sys
from wagtail.utils.deprecation import MovedDefinitionHandler, RemovedInWagtail29Warning

MOVED_DEFINITIONS = {
    'reject_request': 'wagtail.admin.auth',
    'require_admin_access': 'wagtail.admin.auth',
}

sys.modules[__name__] = MovedDefinitionHandler(sys.modules[__name__], MOVED_DEFINITIONS, RemovedInWagtail29Warning)
