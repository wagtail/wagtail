import sys
from wagtail.utils.deprecation import MovedDefinitionHandler, RemovedInWagtail210Warning

MOVED_DEFINITIONS = {
    'DocumentsAPIEndpoint': ('wagtail.documents.api.v2.views', 'DocumentsAPIViewSet'),
}

sys.modules[__name__] = MovedDefinitionHandler(sys.modules[__name__], MOVED_DEFINITIONS, RemovedInWagtail210Warning)
