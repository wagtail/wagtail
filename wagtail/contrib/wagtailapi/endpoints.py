from __future__ import absolute_import

from collections import OrderedDict

from django.db import models
from django.shortcuts import get_object_or_404
from django.conf.urls import url
from django.conf import settings
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
from .utils import BadRequestError, URLPath, ObjectDetailURL


class BaseAPIEndpoint(GenericViewSet):
    renderer_classes = [WagtailJSONRenderer]
    pagination_class = WagtailPagination
    serializer_class = WagtailSerializer
    filter_classes = []

    known_query_parameters = frozenset([
        'limit',
        'offset',
        'fields',
        'order',
        'search',
    ])
    extra_api_fields = []

    def handle_exception(self, exc):
        if isinstance(exc, Http404):
            data = {'message': str(exc)}
            return Response(data, status=status.HTTP_404_NOT_FOUND)
        elif isinstance(exc, BadRequestError):
            data = {'message': str(exc)}
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return super(BaseAPIEndpoint, self).handle_exception(exc)

    def listing_view(self, request):
        return NotImplemented

    def detail_view(self, request, pk):
        return NotImplemented

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

    def get_fields(self, request):
        """
        Return the set of fields that should be returned in the output
        representation for listing views.
        """
        if 'fields' in request.GET:
            return set(request.GET['fields'].split(','))
        return {'title'}

    def get_serializer_context(self):
        """
        The serialization context differs between listing and detail views.
        """
        request = self.request
        if self.action == 'listing_view':
            return {
                'request': request,
                'view': self,
                'fields': self.get_fields(request)
            }
        return {
            'request': request,
            'view': self,
            'all_fields': True,
            'show_details': True
        }

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
    name = 'pages'
    known_query_parameters = BaseAPIEndpoint.known_query_parameters.union([
        'type',
        'child_of',
        'descendant_of',
    ])
    extra_api_fields = ['title']
    filter_backends = [
        FieldsFilter, ChildOfFilter, DescendantOfFilter,
        OrderingFilter, SearchFilter
    ]
    serializer_class = PageSerializer

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

    def listing_view(self, request):
        # Get model and queryset
        queryset = self.get_queryset()

        # Check query paramters
        self.check_query_parameters(queryset)

        # Filtering, Ancestor/Descendant, Ordering, Search.
        queryset = self.filter_queryset(queryset)

        # Pagination
        queryset = self.paginate_queryset(queryset)

        serializer = self.get_serializer(queryset, many=True)
        return self.get_paginated_response(serializer.data)

    def detail_view(self, request, pk):
        page = self.get_object()
        serializer = self.get_serializer(page)
        return Response(serializer.data)

    @classmethod
    def has_model(cls, model):
        return issubclass(model, Page)


class ImagesAPIEndpoint(BaseAPIEndpoint):
    name = 'images'
    model = get_image_model()
    filter_backends = [FieldsFilter, OrderingFilter, SearchFilter]
    extra_api_fields = ['title', 'tags', 'width', 'height']
    queryset =  get_image_model().objects.all().order_by('id')

    def listing_view(self, request):
        queryset = self.get_queryset()

        # Check query paramters
        self.check_query_parameters(queryset)

        # Filtering, Ordering, Search.
        queryset = self.filter_queryset(queryset)

        # Pagination
        queryset = self.paginate_queryset(queryset)

        serializer = self.get_serializer(queryset, many=True)
        return self.get_paginated_response(serializer.data)

    def detail_view(self, request, pk):
        image = self.get_object()
        serializer = self.get_serializer(image)
        return Response(serializer.data)

    @classmethod
    def has_model(cls, model):
        return model == get_image_model()


class DocumentsAPIEndpoint(BaseAPIEndpoint):
    name = 'documents'
    filter_backends = [FieldsFilter, OrderingFilter, SearchFilter]
    extra_api_fields = ['title', 'tags']
    serializer_class = DocumentSerializer
    queryset = Document.objects.all().order_by('id')

    def listing_view(self, request):
        queryset = self.get_queryset()

        # Check query paramters
        self.check_query_parameters(queryset)

        # Filtering, Ordering, Search.
        queryset = self.filter_queryset(queryset)

        # Pagination
        queryset = self.paginate_queryset(queryset)

        serializer = self.get_serializer(queryset, many=True)
        return self.get_paginated_response(serializer.data)

    def detail_view(self, request, pk):
        document = self.get_object()
        serializer = self.get_serializer(document)
        return Response(serializer.data)

    @classmethod
    def has_model(cls, model):
        return model == Document
