import sys
from wagtail.utils.deprecation import MovedDefinitionHandler, RemovedInWagtail210Warning

MOVED_DEFINITIONS = {
    'ImagesAPIEndpoint': ('wagtail.images.api.v2.views', 'ImagesAPIViewSet'),
}

sys.modules[__name__] = MovedDefinitionHandler(sys.modules[__name__], MOVED_DEFINITIONS, RemovedInWagtail210Warning)
