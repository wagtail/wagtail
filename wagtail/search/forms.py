import sys

from wagtail.utils.deprecation import MovedDefinitionHandler, RemovedInWagtail60Warning

MOVED_DEFINITIONS = {
    "QueryForm": ("wagtail.contrib.search_promotions.forms", "QueryForm"),
}

sys.modules[__name__] = MovedDefinitionHandler(
    sys.modules[__name__],
    MOVED_DEFINITIONS,
    RemovedInWagtail60Warning,
)
