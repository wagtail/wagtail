import sys

from wagtail.utils.deprecation import MovedDefinitionHandler, RemovedInWagtail217Warning


MOVED_DEFINITIONS = {
    'QueryForm': ('wagtail.contrib.search_promotions.forms', 'QueryForm'),
}

sys.modules[__name__] = MovedDefinitionHandler(sys.modules[__name__], MOVED_DEFINITIONS, RemovedInWagtail217Warning)
