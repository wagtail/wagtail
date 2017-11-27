from collections import OrderedDict

from django.conf.urls import url
from django.core.exceptions import FieldDoesNotExist
from django.http import Http404
from django.urls import reverse
from modelcluster.fields import ParentalKey
from rest_framework import status
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from wagtail.api import APIField
from wagtail.core.models import Page

from .filters import (
    FieldsFilter, OrderingFilter, RestrictedChildOfFilter, RestrictedDescendantOfFilter,
    SearchFilter)
from .pagination import WagtailPagination
from .serializers import BaseSerializer, PageSerializer, get_serializer_class
from .utils import (
    BadRequestError, filter_page_type, page_models_from_string, parse_fields_parameter)


class BaseAPIEndpoint(GenericViewSet):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

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
    body_fields = ['id']
    meta_fields = ['type', 'detail_url']
    listing_default_fields = ['id', 'type', 'detail_url']
    nested_default_fields = ['id', 'type', 'detail_url']
    detail_only_fields = []
    name = None  # Set on subclass.

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # seen_types is a mapping of type name strings (format: "app_label.ModelName")
        # to model classes. When an object is serialised in the API, its model
        # is added to this mapping. This is used by the Admin API which appends a
        # summary of the used types to the response.
        self.seen_types = OrderedDict()

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
        return super().handle_exception(exc)

    @classmethod
    def _convert_api_fields(cls, fields):
        return [field if isinstance(field, APIField) else APIField(field)
                for field in fields]

    @classmethod
    def get_body_fields(cls, model):
        return cls._convert_api_fields(cls.body_fields + list(getattr(model, 'api_fields', ())))

    @classmethod
    def get_body_fields_names(cls, model):
        return [field.name for field in cls.get_body_fields(model)]

    @classmethod
    def get_meta_fields(cls, model):
        return cls._convert_api_fields(cls.meta_fields + list(getattr(model, 'api_meta_fields', ())))

    @classmethod
    def get_meta_fields_names(cls, model):
        return [field.name for field in cls.get_meta_fields(model)]

    @classmethod
    def get_field_serializer_overrides(cls, model):
        return {field.name: field.serializer
                for field in cls.get_body_fields(model) + cls.get_meta_fields(model)
                if field.serializer is not None}

    @classmethod
    def get_available_fields(cls, model, db_fields_only=False):
        """
        Returns a list of all the fields that can be used in the API for the
        specified model class.

        Setting db_fields_only to True will remove all fields that do not have
        an underlying column in the database (eg, type/detail_url and any custom
        fields that are callables)
        """
        fields = cls.get_body_fields_names(model) + cls.get_meta_fields_names(model)

        if db_fields_only:
            # Get list of available database fields then remove any fields in our
            # list that isn't a database field
            database_fields = set()
            for field in model._meta.get_fields():
                database_fields.add(field.name)

                if hasattr(field, 'attname'):
                    database_fields.add(field.attname)

            fields = [field for field in fields if field in database_fields]

        return fields

    @classmethod
    def get_detail_default_fields(cls, model):
        return cls.get_available_fields(model)

    @classmethod
    def get_listing_default_fields(cls, model):
        return cls.listing_default_fields[:]

    @classmethod
    def get_nested_default_fields(cls, model):
        return cls.nested_default_fields[:]

    def check_query_parameters(self, queryset):
        """
        Ensure that only valid query paramters are included in the URL.
        """
        query_parameters = set(self.request.GET.keys())

        # All query paramters must be either a database field or an operation
        allowed_query_parameters = set(self.get_available_fields(queryset.model, db_fields_only=True)).union(self.known_query_parameters)
        unknown_parameters = query_parameters - allowed_query_parameters
        if unknown_parameters:
            raise BadRequestError("query parameter is not an operation or a recognised field: %s" % ', '.join(sorted(unknown_parameters)))

    @classmethod
    def _get_serializer_class(cls, router, model, fields_config, show_details=False, nested=False):
        # Get all available fields
        body_fields = cls.get_body_fields_names(model)
        meta_fields = cls.get_meta_fields_names(model)
        all_fields = body_fields + meta_fields

        # Remove any duplicates
        all_fields = list(OrderedDict.fromkeys(all_fields))

        if not show_details:
            # Remove detail only fields
            for field in cls.detail_only_fields:
                try:
                    all_fields.remove(field)
                except KeyError:
                    pass

        # Get list of configured fields
        if show_details:
            fields = set(cls.get_detail_default_fields(model))
        elif nested:
            fields = set(cls.get_nested_default_fields(model))
        else:
            fields = set(cls.get_listing_default_fields(model))

        # If first field is '*' start with all fields
        # If first field is '_' start with no fields
        if fields_config and fields_config[0][0] == '*':
            fields = set(all_fields)
            fields_config = fields_config[1:]
        elif fields_config and fields_config[0][0] == '_':
            fields = set()
            fields_config = fields_config[1:]

        mentioned_fields = set()
        sub_fields = {}

        for field_name, negated, field_sub_fields in fields_config:
            if negated:
                try:
                    fields.remove(field_name)
                except KeyError:
                    pass
            else:
                fields.add(field_name)
                if field_sub_fields:
                    sub_fields[field_name] = field_sub_fields

            mentioned_fields.add(field_name)

        unknown_fields = mentioned_fields - set(all_fields)

        if unknown_fields:
            raise BadRequestError("unknown fields: %s" % ', '.join(sorted(unknown_fields)))

        # Build nested serialisers
        child_serializer_classes = {}

        for field_name in fields:
            try:
                django_field = model._meta.get_field(field_name)
            except FieldDoesNotExist:
                django_field = None

            if django_field and django_field.is_relation:
                child_sub_fields = sub_fields.get(field_name, [])

                # Inline (aka "child") models should display all fields by default
                if isinstance(getattr(django_field, 'field', None), ParentalKey):
                    if not child_sub_fields or child_sub_fields[0][0] not in ['*', '_']:
                        child_sub_fields = list(child_sub_fields)
                        child_sub_fields.insert(0, ('*', False, None))

                # Get a serializer class for the related object
                child_model = django_field.related_model
                child_endpoint_class = router.get_model_endpoint(child_model)
                child_endpoint_class = child_endpoint_class[1] if child_endpoint_class else BaseAPIEndpoint
                child_serializer_classes[field_name] = child_endpoint_class._get_serializer_class(router, child_model, child_sub_fields, nested=True)

            else:
                if field_name in sub_fields:
                    # Sub fields were given for a non-related field
                    raise BadRequestError("'%s' does not support nested fields" % field_name)

        # Reorder fields so it matches the order of all_fields
        fields = [field for field in all_fields if field in fields]

        field_serializer_overrides = {field[0]: field[1] for field in cls.get_field_serializer_overrides(model).items() if field[0] in fields}
        return get_serializer_class(
            model,
            fields,
            meta_fields=meta_fields,
            field_serializer_overrides=field_serializer_overrides,
            child_serializer_classes=child_serializer_classes,
            base=cls.base_serializer_class
        )

    def get_serializer_class(self):
        request = self.request

        # Get model
        if self.action == 'listing_view':
            model = self.get_queryset().model
        else:
            model = type(self.get_object())

        # Fields
        if 'fields' in request.GET:
            try:
                fields_config = parse_fields_parameter(request.GET['fields'])
            except ValueError as e:
                raise BadRequestError("fields error: %s" % str(e))
        else:
            # Use default fields
            fields_config = []

        # Allow "detail_only" (eg parent) fields on detail view
        if self.action == 'listing_view':
            show_details = False
        else:
            show_details = True

        return self._get_serializer_class(self.request.wagtailapi_router, model, fields_config, show_details=show_details)

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
        context = super().get_renderer_context()
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
    def get_model_listing_urlpath(cls, model, namespace=''):
        if namespace:
            url_name = namespace + ':listing'
        else:
            url_name = 'listing'

        return reverse(url_name)

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
    body_fields = BaseAPIEndpoint.body_fields + [
        'title',
    ]
    meta_fields = BaseAPIEndpoint.meta_fields + [
        'html_url',
        'slug',
        'show_in_menus',
        'seo_title',
        'search_description',
        'first_published_at',
        'parent',
    ]
    listing_default_fields = BaseAPIEndpoint.listing_default_fields + [
        'title',
        'html_url',
        'slug',
        'first_published_at',
    ]
    nested_default_fields = BaseAPIEndpoint.nested_default_fields + [
        'title',
    ]
    detail_only_fields = ['parent']
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
        if request.site:
            queryset = queryset.descendant_of(request.site.root_page, inclusive=True)
        else:
            # No sites configured
            queryset = queryset.none()

        return queryset

    def get_object(self):
        base = super().get_object()
        return base.specific
