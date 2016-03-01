from collections import OrderedDict

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

    extra_meta_fields = PagesAPIEndpoint.extra_meta_fields + [
        'latest_revision_created_at',
        'status',
        'children',
    ]

    default_fields = PagesAPIEndpoint.default_fields + [
        'latest_revision_created_at',
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

    def get_type_info(self):
        types = OrderedDict()

        for name, model in self.seen_types.items():
            types[name] = OrderedDict([
                ('verbose_name', model._meta.verbose_name),
                ('verbose_name_plural', model._meta.verbose_name_plural),
            ])

        return types

    def listing_view(self, request):
        response = super(PagesAdminAPIEndpoint, self).listing_view(request)
        response.data['__types'] = self.get_type_info()
        return response

    def detail_view(self, request, pk):
        response = super(PagesAdminAPIEndpoint, self).detail_view(request, pk)
        response.data['__types'] = self.get_type_info()
        return response


class ImagesAdminAPIEndpoint(ImagesAPIEndpoint):
    base_serializer_class = AdminImageSerializer

    extra_body_fields = ImagesAPIEndpoint.extra_body_fields + [
        'thumbnail',
    ]

    default_fields = ImagesAPIEndpoint.default_fields + [
        'width',
        'height',
        'thumbnail',
    ]



class DocumentsAdminAPIEndpoint(DocumentsAPIEndpoint):
    pass
