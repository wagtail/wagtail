from __future__ import absolute_import, unicode_literals

from collections import OrderedDict

from django.apps import apps
from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.http import Http404
from rest_framework import status
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from wagtail.wagtailcore.models import Page
from wagtail.wagtaildocs.models import get_document_model
from wagtail.wagtailimages.models import get_image_model

from .filters import (
    FieldsFilter, OrderingFilter, RestrictedChildOfFilter, RestrictedDescendantOfFilter,
    SearchFilter)
from .pagination import WagtailPagination
from .serializers import (
    BaseSerializer, DocumentSerializer, ImageSerializer, PageSerializer, get_serializer_class)
from .utils import BadRequestError, filter_page_type, page_models_from_string


class BaseAPIEndpoint(GenericViewSet):
    renderer_classes = [JSONRenderer]

    # The BrowsableAPIRenderer requires rest_framework to be installed
    # Remove this check in Wagtail 1.4 as rest_framework will be required
    # RemovedInWagtail14Warning
    if apps.is_installed('rest_framework'):
        renderer_classes.append(BrowsableAPIRenderer)

    pagination_class = WagtailPagination
    base_serializer_class = BaseSerializer
    filter_backends = []
    model = None  # Set on subclass

    known_query_parameters = frozenset([
        'limit',
        'offset',
        'fields',
        'order',
        'search',
        'search_operator',

        # Used by jQuery for cache-busting. See #1671
        '_',

        # Required by BrowsableAPIRenderer
        'format',
    ])
    extra_body_fields = []
    extra_meta_fields = []
    default_fields = []
    name = None  # Set on subclass.

    def get_queryset(self):
        return self.model.objects.all().order_by('id')

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

    def get_body_fields(self, model):
        """
        This returns a list of field names that are allowed to
        be used in the API (excluding the id field)
        """
        fields = self.extra_body_fields[:]

        if hasattr(model, 'api_fields'):
            fields.extend(model.api_fields)

        return fields

    def get_meta_fields(self, model):
        """
        This returns a list of field names that are allowed to
        be used in the meta section in the API (excluding type and detail_url).
        """
        meta_fields = self.extra_meta_fields[:]

        if hasattr(model, 'api_meta_fields'):
            meta_fields.extend(model.api_meta_fields)

        return meta_fields

    def get_available_fields(self, model):
        return self.get_body_fields(model) + self.get_meta_fields(model)

    def get_default_fields(self, model):
        return self.default_fields

    def check_query_parameters(self, queryset):
        """
        Ensure that only valid query paramters are included in the URL.
        """
        query_parameters = set(self.request.GET.keys())

        # All query paramters must be either a field or an operation
        allowed_query_parameters = set(self.get_available_fields(queryset.model)).union(self.known_query_parameters).union({'id'})
        unknown_parameters = query_parameters - allowed_query_parameters
        if unknown_parameters:
            raise BadRequestError("query parameter is not an operation or a recognised field: %s" % ', '.join(sorted(unknown_parameters)))

    def get_serializer_class(self):
        request = self.request

        # Get model
        if self.action == 'listing_view':
            model = self.get_queryset().model
        else:
            model = type(self.get_object())

        # Get all available fields
        body_fields = self.get_body_fields(model)
        meta_fields = self.get_meta_fields(model)
        all_fields = body_fields + meta_fields

        # Remove any duplicates
        all_fields = list(OrderedDict.fromkeys(all_fields))

        if self.action == 'listing_view':
            # Listing views just show the title field and any other allowed field the user specified
            if 'fields' in request.GET:
                fields = set(request.GET['fields'].split(','))
            else:
                fields = set(self.get_default_fields(model))

            unknown_fields = fields - set(all_fields)

            if unknown_fields:
                raise BadRequestError("unknown fields: %s" % ', '.join(sorted(unknown_fields)))

            # Reorder fields so it matches the order of all_fields
            fields = [field for field in all_fields if field in fields]
        else:
            # Detail views show all fields all the time
            fields = all_fields

        # If showing details, add the parent field
        if isinstance(self, PagesAPIEndpoint) and self.action == 'detail_view':
            fields.insert(2, 'parent')

        return get_serializer_class(model, fields, meta_fields=meta_fields, base=self.base_serializer_class)

    def get_serializer_context(self):
        """
        The serialization context differs between listing and detail views.
        """
        return {
            'request': self.request,
            'view': self,
            'router': self.request.wagtailapi_router
        }

    def get_renderer_context(self):
        context = super(BaseAPIEndpoint, self).get_renderer_context()
        context['indent'] = 4
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
    def get_object_detail_urlpath(cls, model, pk, namespace=''):
        if namespace:
            url_name = namespace + ':detail'
        else:
            url_name = 'detail'

        return reverse(url_name, args=(pk, ))


class PagesAPIEndpoint(BaseAPIEndpoint):
    base_serializer_class = PageSerializer
    filter_backends = [
        FieldsFilter,
        RestrictedChildOfFilter,
        RestrictedDescendantOfFilter,
        OrderingFilter,
        SearchFilter
    ]
    known_query_parameters = BaseAPIEndpoint.known_query_parameters.union([
        'type',
        'child_of',
        'descendant_of',
    ])
    extra_body_fields = [
        'title',
    ]
    extra_meta_fields = [
        'slug',
        'show_in_menus',
        'seo_title',
        'search_description',
        'first_published_at',
    ]
    default_fields = [
        'title',
        'slug',
        'first_published_at',
    ]
    name = 'pages'
    model = Page

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

        # Get live pages that are not in a private section
        queryset = queryset.public().live()

        # Filter by site
        queryset = queryset.descendant_of(request.site.root_page, inclusive=True)

        return queryset

    def get_object(self):
        base = super(PagesAPIEndpoint, self).get_object()
        return base.specific


class ImagesAPIEndpoint(BaseAPIEndpoint):
    base_serializer_class = ImageSerializer
    filter_backends = [FieldsFilter, OrderingFilter, SearchFilter]
    extra_body_fields = ['title', 'width', 'height']
    extra_meta_fields = ['tags']
    default_fields = ['title', 'tags']
    name = 'images'
    model = get_image_model()


class DocumentsAPIEndpoint(BaseAPIEndpoint):
    base_serializer_class = DocumentSerializer
    filter_backends = [FieldsFilter, OrderingFilter, SearchFilter]
    extra_body_fields = ['title']
    extra_meta_fields = ['tags', ]
    default_fields = ['title', 'tags']
    name = 'documents'
    model = get_document_model()
