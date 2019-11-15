import sys
from wagtail.utils.deprecation import MovedDefinitionHandler, RemovedInWagtail210Warning

MOVED_DEFINITIONS = {
    'BaseAPIEndpoint': ('wagtail.api.v2.views', 'BaseAPIViewSet'),
    'PagesAPIEndpoint': ('wagtail.api.v2.views', 'PagesAPIViewSet'),
}

sys.modules[__name__] = MovedDefinitionHandler(sys.modules[__name__], MOVED_DEFINITIONS, RemovedInWagtail210Warning)
