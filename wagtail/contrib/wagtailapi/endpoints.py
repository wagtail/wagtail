from __future__ import absolute_import

from collections import OrderedDict

from modelcluster.models import get_all_child_relations
from taggit.managers import _TaggableManager

from django.db import models
from django.utils.encoding import force_text
from django.shortcuts import get_object_or_404
from django.conf.urls import url
from django.conf import settings

from wagtail.wagtailcore.models import Page
from wagtail.wagtailimages.models import get_image_model
from wagtail.wagtaildocs.models import Document
from wagtail.wagtailcore.utils import resolve_model_string
from wagtail.wagtailsearch.backends import get_search_backend
from wagtail.utils.compat import get_related_model

from .utils import BadRequestError


class URLPath(object):
    """
    This class represents a URL path that should be converted to a full URL.

    It is used when the domain that should be used is not known at the time
    the URL was generated. It will get resolved to a full URL during
    serialisation in api.py.

    One example use case is the documents endpoint adding download URLs into
    the JSON. The endpoint does not know the domain name to use at the time so
    returns one of these instead.
    """
    def __init__(self, path):
        self.path = path


class ObjectDetailURL(object):
    def __init__(self, model, pk):
        self.model = model
        self.pk = pk


def get_api_data(obj, fields):
    # Find any child relations (pages only)
    child_relations = {}
    if isinstance(obj, Page):
        child_relations = {
            child_relation.field.rel.related_name: get_related_model(child_relation)
            for child_relation in get_all_child_relations(type(obj))
        }

    # Loop through fields
    for field_name in fields:
        # Check child relations
        if field_name in child_relations and hasattr(child_relations[field_name], 'api_fields'):
            yield field_name, [
                dict(get_api_data(child_object, child_relations[field_name].api_fields))
                for child_object in getattr(obj, field_name).all()
            ]
            continue

        # Check django fields
        try:
            field = obj._meta.get_field_by_name(field_name)[0]

            if field.rel and isinstance(field.rel, models.ManyToOneRel):
                # Foreign key
                val = field._get_val_from_obj(obj)

                if val:
                    yield field_name, OrderedDict([
                        ('id', field._get_val_from_obj(obj)),
                        ('meta', OrderedDict([
                             ('type', field.rel.to._meta.app_label + '.' + field.rel.to.__name__),
                             ('detail_url', ObjectDetailURL(field.rel.to, val)),
                        ])),
                    ])
                else:
                    yield field_name, None
            else:
                yield field_name, field._get_val_from_obj(obj)

            continue
        except models.fields.FieldDoesNotExist:
            pass

        # Check attributes
        if hasattr(obj, field_name):
            value = getattr(obj, field_name)
            yield field_name, force_text(value, strings_only=True)
            continue


class BaseAPIEndpoint(object):
    known_query_parameters = frozenset([
        'limit',
        'offset',
        'fields',
        'order',
        'search',
    ])

    def listing_view(self, request):
        return NotImplemented

    def detail_view(self, request, pk):
        return NotImplemented

    def get_api_fields(self, model):
        """
        This returns a list of field names that are allowed to
        be used in the API (excluding the id field).
        """
        api_fields = []

        if hasattr(model, 'api_fields'):
            api_fields.extend(model.api_fields)

        return api_fields

    def serialize_object_metadata(self, request, obj, show_details=False):
        """
        This returns a JSON-serialisable dict to use for the "meta"
        section of a particlular object.
        """
        data = OrderedDict()

        # Add type
        data['type'] = type(obj)._meta.app_label + '.' + type(obj).__name__
        data['detail_url'] = ObjectDetailURL(type(obj), obj.pk)

        return data

    def serialize_object(self, request, obj, fields=frozenset(), extra_data=(), all_fields=False, show_details=False):
        """
        This converts an object into JSON-serialisable dict so it can
        be used in the API.
        """
        data = [
            ('id', obj.id),
        ]

        # Add meta
        metadata = self.serialize_object_metadata(request, obj, show_details=show_details)
        if metadata:
            data.append(('meta', metadata))

        # Add extra data
        data.extend(extra_data)

        # Add other fields
        api_fields = self.get_api_fields(type(obj))
        api_fields = list(OrderedDict.fromkeys(api_fields)) # Removes any duplicates in case the user put "title" in api_fields

        if all_fields:
            fields = api_fields
        else:
            unknown_fields = fields - set(api_fields)

            if unknown_fields:
                raise BadRequestError("unknown fields: %s" % ', '.join(sorted(unknown_fields)))

            # Reorder fields so it matches the order of api_fields
            fields = [field for field in api_fields if field in fields]

        data.extend(get_api_data(obj, fields))

        return OrderedDict(data)

    def check_query_parameters(self, request, queryset):
        query_parameters = set(request.GET.keys())

        # All query paramters must be either a field or an operation
        allowed_query_parameters = set(self.get_api_fields(queryset.model)).union(self.known_query_parameters).union({'id'})
        unknown_parameters = query_parameters - allowed_query_parameters
        if unknown_parameters:
            raise BadRequestError("query parameter is not an operation or a recognised field: %s" % ', '.join(sorted(unknown_parameters)))

    def do_field_filtering(self, request, queryset):
        """
        This performs field level filtering on the result set
        Eg: ?title=James Joyce
        """
        fields = set(self.get_api_fields(queryset.model)).union({'id'})

        for field_name, value in request.GET.items():
            if field_name in fields:
                field = getattr(queryset.model, field_name, None)

                if isinstance(field, _TaggableManager):
                    for tag in value.split(','):
                        queryset = queryset.filter(**{field_name + '__name': tag})

                    # Stick a message on the queryset to indicate that tag filtering has been performed
                    # This will let the do_search method know that it must raise an error as searching
                    # and tag filtering at the same time is not supported
                    queryset._filtered_by_tag = True
                else:
                    queryset = queryset.filter(**{field_name: value})

        return queryset

    def do_ordering(self, request, queryset):
        """
        This applies ordering to the result set
        Eg: ?order=title

        It also supports reverse ordering
        Eg: ?order=-title

        And random ordering
        Eg: ?order=random
        """
        if 'order' in request.GET:
            # Prevent ordering while searching
            if 'search' in request.GET:
                raise BadRequestError("ordering with a search query is not supported")

            order_by = request.GET['order']

            # Random ordering
            if order_by == 'random':
                # Prevent ordering by random with offset
                if 'offset' in request.GET:
                    raise BadRequestError("random ordering with offset is not supported")

                return queryset.order_by('?')

            # Check if reverse ordering is set
            if order_by.startswith('-'):
                reverse_order = True
                order_by = order_by[1:]
            else:
                reverse_order = False

            # Add ordering
            if order_by == 'id' or order_by in self.get_api_fields(queryset.model):
                queryset = queryset.order_by(order_by)
            else:
                # Unknown field
                raise BadRequestError("cannot order by '%s' (unknown field)" % order_by)

            # Reverse order
            if reverse_order:
                queryset = queryset.reverse()

        return queryset

    def do_search(self, request, queryset):
        """
        This performs a full-text search on the result set
        Eg: ?search=James Joyce
        """
        search_enabled = getattr(settings, 'WAGTAILAPI_SEARCH_ENABLED', True)

        if 'search' in request.GET:
            if not search_enabled:
                raise BadRequestError("search is disabled")

            # Searching and filtering by tag at the same time is not supported
            if getattr(queryset, '_filtered_by_tag', False):
                raise BadRequestError("filtering by tag with a search query is not supported")

            search_query = request.GET['search']

            sb = get_search_backend()
            queryset = sb.search(search_query, queryset)

        return queryset

    def do_pagination(self, request, queryset):
        """
        This performs limit/offset based pagination on the result set
        Eg: ?limit=10&offset=20 -- Returns 10 items starting at item 20
        """
        limit_max = getattr(settings, 'WAGTAILAPI_LIMIT_MAX', 20)

        try:
            offset = int(request.GET.get('offset', 0))
            assert offset >= 0
        except (ValueError, AssertionError):
            raise BadRequestError("offset must be a positive integer")

        try:
            limit = int(request.GET.get('limit', min(20, limit_max)))

            if limit > limit_max:
                raise BadRequestError("limit cannot be higher than %d" % limit_max)

            assert limit >= 0
        except (ValueError, AssertionError):
            raise BadRequestError("limit must be a positive integer")

        start = offset
        stop = offset + limit

        return queryset[start:stop]

    def get_urlpatterns(self):
        """
        This returns a list of URL patterns for the endpoint
        """
        return [
            url(r'^$', self.listing_view, name='listing'),
            url(r'^(\d+)/$', self.detail_view, name='detail'),
        ]

    def has_model(self, model):
        return False


class PagesAPIEndpoint(BaseAPIEndpoint):
    known_query_parameters = BaseAPIEndpoint.known_query_parameters.union([
        'type',
        'child_of',
    ])

    def get_queryset(self, request, model=Page):
        # Get live pages that are not in a private section
        queryset = model.objects.public().live()

        # Filter by site
        queryset = queryset.descendant_of(request.site.root_page, inclusive=True)

        return queryset

    def get_api_fields(self, model):
        api_fields = ['title']
        api_fields.extend(super(PagesAPIEndpoint, self).get_api_fields(model))
        return api_fields

    def serialize_object_metadata(self, request, page, show_details=False):
        data = super(PagesAPIEndpoint, self).serialize_object_metadata(request, page, show_details=show_details)

        # Add type
        data['type'] = page.specific_class._meta.app_label + '.' + page.specific_class.__name__

        return data

    def serialize_object(self, request, page, fields=frozenset(), extra_data=(), all_fields=False, show_details=False):
        # Add parent
        if show_details:
            parent = page.get_parent()

            # Make sure the parent is visible in the API
            if self.get_queryset(request).filter(id=parent.id).exists():
                parent_class = parent.specific_class

                extra_data += (
                    ('parent', OrderedDict([
                        ('id', parent.id),
                        ('meta', OrderedDict([
                             ('type', parent_class._meta.app_label + '.' + parent_class.__name__),
                             ('detail_url', ObjectDetailURL(parent_class, parent.id)),
                        ])),
                    ])),
                )

        return super(PagesAPIEndpoint, self).serialize_object(request, page, fields=fields, extra_data=extra_data, all_fields=all_fields, show_details=show_details)

    def get_model(self, request):
        if 'type' not in request.GET:
            return Page

        model_name = request.GET['type']
        try:
            model = resolve_model_string(model_name)

            if not issubclass(model, Page):
                raise BadRequestError("type doesn't exist")

            return model
        except LookupError:
            raise BadRequestError("type doesn't exist")

    def do_child_of_filter(self, request, queryset):
        if 'child_of' in request.GET:
            try:
                parent_page_id = int(request.GET['child_of'])
                assert parent_page_id >= 0
            except (ValueError, AssertionError):
                raise BadRequestError("child_of must be a positive integer")

            try:
                parent_page = self.get_queryset(request).get(id=parent_page_id)
                return queryset.child_of(parent_page)
            except Page.DoesNotExist:
                raise BadRequestError("parent page doesn't exist")

        return queryset

    def listing_view(self, request):
        # Get model and queryset
        model = self.get_model(request)
        queryset = self.get_queryset(request, model=model)

        # Check query paramters
        self.check_query_parameters(request, queryset)

        # Filtering
        queryset = self.do_field_filtering(request, queryset)
        queryset = self.do_child_of_filter(request, queryset)

        # Ordering
        queryset = self.do_ordering(request, queryset)

        # Search
        queryset = self.do_search(request, queryset)

        # Pagination
        total_count = queryset.count()
        queryset = self.do_pagination(request, queryset)

        # Get list of fields to show in results
        if 'fields' in request.GET:
            fields = set(request.GET['fields'].split(','))
        else:
            fields = {'title'}

        return OrderedDict([
            ('meta', OrderedDict([
                ('total_count', total_count),
            ])),
            ('pages', [
                self.serialize_object(request, page, fields=fields)
                for page in queryset
            ]),
        ])

    def detail_view(self, request, pk):
        page = get_object_or_404(self.get_queryset(request), pk=pk).specific
        return self.serialize_object(request, page, all_fields=True, show_details=True)

    def has_model(self, model):
        return issubclass(model, Page)


class ImagesAPIEndpoint(BaseAPIEndpoint):
    model = get_image_model()

    def get_queryset(self, request):
        return self.model.objects.all()

    def get_api_fields(self, model):
        api_fields = ['title', 'tags', 'width', 'height']
        api_fields.extend(super(ImagesAPIEndpoint, self).get_api_fields(model))
        return api_fields

    def listing_view(self, request):
        queryset = self.get_queryset(request)

        # Check query paramters
        self.check_query_parameters(request, queryset)

        # Filtering
        queryset = self.do_field_filtering(request, queryset)

        # Ordering
        queryset = self.do_ordering(request, queryset)

        # Search
        queryset = self.do_search(request, queryset)

        # Pagination
        total_count = queryset.count()
        queryset = self.do_pagination(request, queryset)

        # Get list of fields to show in results
        if 'fields' in request.GET:
            fields = set(request.GET['fields'].split(','))
        else:
            fields = {'title'}

        return OrderedDict([
            ('meta', OrderedDict([
                ('total_count', total_count),
            ])),
            ('images', [
                self.serialize_object(request, image, fields=fields)
                for image in queryset
            ]),
        ])

    def detail_view(self, request, pk):
        image = get_object_or_404(self.get_queryset(request), pk=pk)
        return self.serialize_object(request, image, all_fields=True)

    def has_model(self, model):
        return model == self.model


class DocumentsAPIEndpoint(BaseAPIEndpoint):
    def get_api_fields(self, model):
        api_fields = ['title', 'tags']
        api_fields.extend(super(DocumentsAPIEndpoint, self).get_api_fields(model))
        return api_fields

    def serialize_object_metadata(self, request, document, show_details=False):
        data = super(DocumentsAPIEndpoint, self).serialize_object_metadata(request, document, show_details=show_details)

        # Download URL
        if show_details:
            data['download_url'] = URLPath(document.url)

        return data

    def listing_view(self, request):
        queryset = Document.objects.all()

        # Check query paramters
        self.check_query_parameters(request, queryset)

        # Filtering
        queryset = self.do_field_filtering(request, queryset)

        # Ordering
        queryset = self.do_ordering(request, queryset)

        # Search
        queryset = self.do_search(request, queryset)

        # Pagination
        total_count = queryset.count()
        queryset = self.do_pagination(request, queryset)

        # Get list of fields to show in results
        if 'fields' in request.GET:
            fields = set(request.GET['fields'].split(','))
        else:
            fields = {'title'}

        return OrderedDict([
            ('meta', OrderedDict([
                ('total_count', total_count),
            ])),
            ('documents', [
                self.serialize_object(request, document, fields=fields)
                for document in queryset
            ]),
        ])

    def detail_view(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        return self.serialize_object(request, document, all_fields=True, show_details=True)

    def has_model(self, model):
        return model == Document
