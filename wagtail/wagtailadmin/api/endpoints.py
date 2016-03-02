from wagtail.api.v2.utils import BadRequestError, page_models_from_string, filter_page_type
from wagtail.api.v2.endpoints import PagesAPIEndpoint, ImagesAPIEndpoint, DocumentsAPIEndpoint
from wagtail.api.v2.filters import (
    FieldsFilter, OrderingFilter, SearchFilter,
    ChildOfFilter, DescendantOfFilter
)

from wagtail.wagtailcore.models import Page

from .serializers import AdminPageSerializer, AdminImageSerializer

from django.db.models import Q


class HasChildrenFilter(ChildOfFilter):
    """
    Filters the queryset by checking if the pages have children or not.
    This is useful when you want to get just the branches or just the leaves.
    """
    def filter_queryset(self, request, queryset, view):
        if 'has_children' in request.GET:
            try:
                has_children_filter = int(request.GET['has_children'])
                assert has_children_filter is 1 or has_children_filter is 0
            except (ValueError, AssertionError):
                raise BadRequestError("has_children must be a boolean value, eg 1 or 0")

            if has_children_filter == 1:
                return queryset.filter(Q(numchild__gt=0))
            else:
                return queryset.filter(Q(numchild=0))
        return queryset



class PagesAdminAPIEndpoint(PagesAPIEndpoint):
    base_serializer_class = AdminPageSerializer

    # Use unrestricted filters
    filter_backends = [
        FieldsFilter,
        ChildOfFilter,
        DescendantOfFilter,
        HasChildrenFilter,
        OrderingFilter,
        SearchFilter
    ]

    extra_meta_fields = PagesAPIEndpoint.extra_meta_fields + [
        'status',
        'children',
    ]

    default_fields = PagesAPIEndpoint.default_fields + [
        'status',
        'children',
    ]

    known_query_parameters = PagesAPIEndpoint.known_query_parameters.union([
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
        # if request.GET.get('include_root', False) is True:
            # queryset = queryset
        # else:
            # queryset = queryset.exclude(depth=1)

        return queryset


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
