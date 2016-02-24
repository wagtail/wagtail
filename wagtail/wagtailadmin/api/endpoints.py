from wagtail.api.v2.utils import BadRequestError, page_models_from_string, filter_page_type
from wagtail.api.v2.endpoints import PagesAPIEndpoint, ImagesAPIEndpoint, DocumentsAPIEndpoint

from wagtail.wagtailcore.models import Page

from .serializers import AdminPageSerializer, AdminImageSerializer


class PagesAdminAPIEndpoint(PagesAPIEndpoint):
    base_serializer_class = AdminPageSerializer

    api_fields = [
        'title',
        'slug',
        'first_published_at',
        'status',
        'children',
        'title',
    ]

    def get_available_fields(self, model):
        return self.api_fields

    def get_queryset(self):
        request = self.request

        # Allow pages to be filtered to a specific type
        try:
            models = page_models_from_string(request.GET.get('type', 'wagtailcore.Page'))
        except (LookupError, ValueError):
            raise BadRequestError("type doesn't exist")

        if not models:
            models = [Page]

        if len(models) == 1:
            queryset = models[0].objects.all()
        else:
            queryset = Page.objects.all()

            # Filter pages by specified models
            queryset = filter_page_type(queryset, models)

        # Hide root page
        # TODO: Add "include_root" flag
        queryset = queryset.exclude(depth=1)

        return queryset


class ImagesAdminAPIEndpoint(ImagesAPIEndpoint):
    base_serializer_class = AdminImageSerializer

    api_fields = [
        'title',
        'tags',
        'width',
        'height',
        'thumbnail',
    ]

    def get_available_fields(self, model):
        return self.api_fields


class DocumentsAdminAPIEndpoint(DocumentsAPIEndpoint):
    api_fields = [
        'title',
        'tags',
    ]

    def get_available_fields(self, model):
        return self.api_fields
