from __future__ import absolute_import

from django.conf.urls import url
from django.http import Http404

from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from wagtail.wagtailcore.models import Page
from wagtail.wagtailimages.models import get_image_model
from wagtail.wagtaildocs.models import Document
from wagtail.wagtailcore.utils import resolve_model_string

from .filters import (
    FieldsFilter, OrderingFilter, SearchFilter,
    ChildOfFilter, DescendantOfFilter
)
from .renderers import WagtailJSONRenderer
from .pagination import WagtailPagination
from .serializers import WagtailSerializer, PageSerializer, DocumentSerializer
from .utils import BadRequestError


class BaseAPIEndpoint(GenericViewSet):
    renderer_classes = [WagtailJSONRenderer]
    pagination_class = WagtailPagination
    serializer_class = WagtailSerializer
    filter_classes = []
    queryset = None  # Set on subclasses or implement `get_queryset()`.

    known_query_parameters = frozenset([
        'limit',
        'offset',
        'fields',
        'order',
        'search',
    ])
    extra_api_fields = []
    name = None  # Set on subclass.

    def listing_view(self, request):
        queryset = self.get_queryset()
        self.check_query_parameters(queryset)
        queryset = self.filter_queryset(queryset)
        queryset = self.paginate_queryset(queryset)
        serializer = self.get_serializer(queryset, many=True)
        return self.get_paginated_response(serializer.data)

    def detail_view(self, request, pk):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def handle_exception(self, exc):
        if isinstance(exc, Http404):
            data = {'message': str(exc)}
            return Response(data, status=status.HTTP_404_NOT_FOUND)
        elif isinstance(exc, BadRequestError):
            data = {'message': str(exc)}
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return super(BaseAPIEndpoint, self).handle_exception(exc)

    def get_api_fields(self, model):
        """
        This returns a list of field names that are allowed to
        be used in the API (excluding the id field).
        """
        api_fields = self.extra_api_fields[:]

        if hasattr(model, 'api_fields'):
            api_fields.extend(model.api_fields)

        return api_fields

    def check_query_parameters(self, queryset):
        """
        Ensure that only valid query paramters are included in the URL.
        """
        query_parameters = set(self.request.GET.keys())

        # All query paramters must be either a field or an operation
        allowed_query_parameters = set(self.get_api_fields(queryset.model)).union(self.known_query_parameters).union({'id'})
        unknown_parameters = query_parameters - allowed_query_parameters
        if unknown_parameters:
            raise BadRequestError("query parameter is not an operation or a recognised field: %s" % ', '.join(sorted(unknown_parameters)))

    def get_serializer_context(self):
        """
        The serialization context differs between listing and detail views.
        """
        request = self.request
        if self.action == 'listing_view':

            if 'fields' in request.GET:
                fields = set(request.GET['fields'].split(','))
            else:
                fields = {'title'}

            return {
                'request': request,
                'view': self,
                'fields': fields
            }

        return {
            'request': request,
            'view': self,
            'all_fields': True,
            'show_details': True
        }

    def get_renderer_context(self):
        context = super(BaseAPIEndpoint, self).get_renderer_context()
        context['endpoints'] = [
            PagesAPIEndpoint,
            ImagesAPIEndpoint,
            DocumentsAPIEndpoint
        ]
        return context

    @classmethod
    def get_urlpatterns(cls):
        """
        This returns a list of URL patterns for the endpoint
        """
        return [
            url(r'^$', cls.as_view({'get': 'listing_view'}), name='listing'),
            url(r'^(?P<pk>\d+)/$', cls.as_view({'get': 'detail_view'}), name='detail'),
        ]

    @classmethod
    def has_model(cls, model):
        return NotImplemented


class PagesAPIEndpoint(BaseAPIEndpoint):
    serializer_class = PageSerializer
    filter_backends = [
        FieldsFilter,
        ChildOfFilter,
        DescendantOfFilter,
        OrderingFilter,
        SearchFilter
    ]
    known_query_parameters = BaseAPIEndpoint.known_query_parameters.union([
        'type',
        'child_of',
        'descendant_of',
    ])
    extra_api_fields = ['title']
    name = 'pages'

    def get_queryset(self):
        request = self.request

        # Allow pages to be filtered to a specific type
        if 'type' not in request.GET:
            model = Page
        else:
            model_name = request.GET['type']
            try:
                model = resolve_model_string(model_name)
            except LookupError:
                raise BadRequestError("type doesn't exist")
            if not issubclass(model, Page):
                raise BadRequestError("type doesn't exist")

        # Get live pages that are not in a private section
        queryset = model.objects.public().live()

        # Filter by site
        queryset = queryset.descendant_of(request.site.root_page, inclusive=True)

        return queryset

    def get_object(self):
        base = super(PagesAPIEndpoint, self).get_object()
        return base.specific

    @classmethod
    def has_model(cls, model):
        return issubclass(model, Page)


class ImagesAPIEndpoint(BaseAPIEndpoint):
    queryset = get_image_model().objects.all().order_by('id')
    filter_backends = [FieldsFilter, OrderingFilter, SearchFilter]
    extra_api_fields = ['title', 'tags', 'width', 'height']
    name = 'images'

    @classmethod
    def has_model(cls, model):
        return model == get_image_model()


class DocumentsAPIEndpoint(BaseAPIEndpoint):
    queryset = Document.objects.all().order_by('id')
    serializer_class = DocumentSerializer
    filter_backends = [FieldsFilter, OrderingFilter, SearchFilter]
    extra_api_fields = ['title', 'tags']
    name = 'documents'

    @classmethod
    def has_model(cls, model):
        return model == Document
