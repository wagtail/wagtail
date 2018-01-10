from collections import OrderedDict

from wagtail.api.v2.endpoints import PagesAPIEndpoint
from wagtail.api.v2.filters import (
    ChildOfFilter, DescendantOfFilter, FieldsFilter, ForExplorerFilter, OrderingFilter,
    SearchFilter)
from wagtail.api.v2.utils import BadRequestError, filter_page_type, page_models_from_string
from wagtail.core.models import Page

from .filters import HasChildrenFilter
from .serializers import AdminPageSerializer


class PagesAdminAPIEndpoint(PagesAPIEndpoint):
    base_serializer_class = AdminPageSerializer

    # Use unrestricted child_of/descendant_of filters
    # Add has_children filter
    filter_backends = [
        FieldsFilter,
        ChildOfFilter,
        DescendantOfFilter,
        ForExplorerFilter,
        HasChildrenFilter,
        OrderingFilter,
        SearchFilter,
    ]

    meta_fields = PagesAPIEndpoint.meta_fields + [
        'latest_revision_created_at',
        'status',
        'children',
        'descendants',
        'parent',
    ]

    body_fields = PagesAPIEndpoint.body_fields + [
        'admin_display_title',
    ]

    listing_default_fields = PagesAPIEndpoint.listing_default_fields + [
        'latest_revision_created_at',
        'status',
        'children',
        'admin_display_title',
    ]

    # Allow the parent field to appear on listings
    detail_only_fields = []

    known_query_parameters = PagesAPIEndpoint.known_query_parameters.union([
        'for_explorer',
        'has_children'
    ])

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
        queryset = queryset.exclude(depth=1).specific()

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
        response = super().listing_view(request)
        response.data['__types'] = self.get_type_info()
        return response

    def detail_view(self, request, pk):
        response = super().detail_view(request, pk)
        response.data['__types'] = self.get_type_info()
        return response
