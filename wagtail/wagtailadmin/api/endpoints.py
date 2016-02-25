from wagtail.api.v2.utils import BadRequestError, page_models_from_string, filter_page_type
from wagtail.api.v2.endpoints import PagesAPIEndpoint, ImagesAPIEndpoint, DocumentsAPIEndpoint
from wagtail.api.v2.filters import (
    FieldsFilter, OrderingFilter, SearchFilter,
    ChildOfFilter, DescendantOfFilter
)

from wagtail.wagtailcore.models import Page

from .serializers import AdminPageSerializer, AdminImageSerializer


class PagesAdminAPIEndpoint(PagesAPIEndpoint):
    base_serializer_class = AdminPageSerializer

    # Use unrestricted filters
    filter_backends = [
        FieldsFilter,
        ChildOfFilter,
        DescendantOfFilter,
        OrderingFilter,
        SearchFilter
    ]

    extra_api_fields = PagesAPIEndpoint.extra_api_fields + [
        'status',
        'children',
    ]

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

    extra_api_fields = ImagesAPIEndpoint.extra_api_fields + [
        'thumbnail',
    ]


class DocumentsAdminAPIEndpoint(DocumentsAPIEndpoint):
    pass
