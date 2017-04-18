from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.db import models
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from rest_framework.filters import BaseFilterBackend
from taggit.managers import TaggableManager

from wagtail.wagtailcore.models import Page
from wagtail.wagtailsearch.backends import get_search_backend
from wagtail.utils.compat import coreapi, coreschema

from .utils import BadRequestError, pages_for_site, parse_boolean


class FieldsFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        """
        This performs field level filtering on the result set
        Eg: ?title=James Joyce
        """
        fields = set(view.get_available_fields(queryset.model, db_fields_only=True))

        for field_name, value in request.GET.items():
            if field_name in fields:
                try:
                    field = queryset.model._meta.get_field(field_name)
                except LookupError:
                    field = None

                # Convert value into python
                try:
                    if isinstance(field, (models.BooleanField, models.NullBooleanField)):
                        value = parse_boolean(value)
                    elif isinstance(field, (models.IntegerField, models.AutoField)):
                        value = int(value)
                except ValueError as e:
                    raise BadRequestError("field filter error. '%s' is not a valid value for %s (%s)" % (
                        value,
                        field_name,
                        str(e)
                    ))

                if isinstance(field, TaggableManager):
                    for tag in value.split(','):
                        queryset = queryset.filter(**{field_name + '__name': tag})

                    # Stick a message on the queryset to indicate that tag filtering has been performed
                    # This will let the do_search method know that it must raise an error as searching
                    # and tag filtering at the same time is not supported
                    queryset._filtered_by_tag = True
                else:
                    queryset = queryset.filter(**{field_name: value})

        return queryset


class OrderingFilter(BaseFilterBackend):
    ordering_param = 'order'
    ordering_title = _('Ordering')
    ordering_description = _('Which field to use when ordering the results.')

    def filter_queryset(self, request, queryset, view):
        """
        This applies ordering to the result set
        Eg: ?order=title

        It also supports reverse ordering
        Eg: ?order=-title

        And random ordering
        Eg: ?order=random
        """
        if self.ordering_param in request.GET:
            order_by = request.GET[self.ordering_param]

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
            if order_by in view.get_available_fields(queryset.model):
                queryset = queryset.order_by(order_by)
            else:
                # Unknown field
                raise BadRequestError("cannot order by '%s' (unknown field)" % order_by)

            # Reverse order
            if reverse_order:
                queryset = queryset.reverse()

        return queryset

    def get_schema_fields(self, view):
        assert coreapi is not None, 'coreapi must be installed to use `get_schema_fields()`'
        assert coreschema is not None, 'coreschema must be installed to use `get_schema_fields()`'
        return [
            coreapi.Field(
                name=self.ordering_param,
                required=False,
                location='query',
                schema=coreschema.String(
                    title=force_text(self.ordering_title),
                    description=force_text(self.ordering_description)
                )
            )
        ]


class SearchFilter(BaseFilterBackend):
    search_param = 'search'
    search_title = _('Search')
    search_description = _('A search term.')

    search_operator_param = 'search_operator'
    search_operator_title = _('Search operator')
    search_operator_description = _('Specifies how multiple terms in the query should be handled.')

    def filter_queryset(self, request, queryset, view):
        """
        This performs a full-text search on the result set
        Eg: ?search=James Joyce
        """
        search_enabled = getattr(settings, 'WAGTAILAPI_SEARCH_ENABLED', True)

        if self.search_param in request.GET:
            if not search_enabled:
                raise BadRequestError("search is disabled")

            # Searching and filtering by tag at the same time is not supported
            if getattr(queryset, '_filtered_by_tag', False):
                raise BadRequestError("filtering by tag with a search query is not supported")

            search_query = request.GET[self.search_param]
            search_operator = request.GET.get(self.search_operator_param, None)
            order_by_relevance = OrderingFilter.ordering_param not in request.GET

            sb = get_search_backend()
            queryset = sb.search(search_query, queryset, operator=search_operator, order_by_relevance=order_by_relevance)

        return queryset

    def get_schema_fields(self, view):
        assert coreapi is not None, 'coreapi must be installed to use `get_schema_fields()`'
        assert coreschema is not None, 'coreschema must be installed to use `get_schema_fields()`'
        return [
            coreapi.Field(
                name=self.search_param,
                required=False,
                location='query',
                schema=coreschema.String(
                    title=force_text(self.search_title),
                    description=force_text(self.search_description)
                )
            ),
            coreapi.Field(
                name=self.search_operator_param,
                required=False,
                location='query',
                # TODO: Use Enum once https://github.com/core-api/python-client/pull/126 merged
                schema=coreschema.String(
                    title=force_text(self.search_operator_title),
                    description=force_text(self.search_operator_description)
                )
            )
        ]


class ChildOfFilter(BaseFilterBackend):
    """
    Implements the ?child_of filter used to filter the results to only contain
    pages that are direct children of the specified page.
    """
    child_of_param = 'child_of'
    child_of_title = _('Direct children of a page')
    child_of_description = _(
        'Id of a page to filters the list of results to contain only direct children of that page.'
    )

    def get_root_page(self, request):
        return Page.get_first_root_node()

    def get_page_by_id(self, request, page_id):
        return Page.objects.get(id=page_id)

    def filter_queryset(self, request, queryset, view):
        if self.child_of_param in request.GET:
            try:
                parent_page_id = int(request.GET[self.child_of_param])
                assert parent_page_id >= 0

                parent_page = self.get_page_by_id(request, parent_page_id)
            except (ValueError, AssertionError):
                if request.GET[self.child_of_param] == 'root':
                    parent_page = self.get_root_page(request)
                else:
                    raise BadRequestError("{} must be a positive integer".format(self.child_of_param))
            except Page.DoesNotExist:
                raise BadRequestError("parent page doesn't exist")

            queryset = queryset.child_of(parent_page)
            queryset._filtered_by_child_of = True

        return queryset

    def get_schema_fields(self, view):
        assert coreapi is not None, 'coreapi must be installed to use `get_schema_fields()`'
        assert coreschema is not None, 'coreschema must be installed to use `get_schema_fields()`'
        return [
            coreapi.Field(
                name=self.child_of_param,
                required=False,
                location='query',
                schema=coreschema.String(
                    title=force_text(self.child_of_title),
                    description=force_text(self.child_of_description)
                )
            )
        ]


class RestrictedChildOfFilter(ChildOfFilter):
    """
    A restricted version of ChildOfFilter that only allows pages in the current
    site to be specified.
    """
    def get_root_page(self, request):
        return request.site.root_page

    def get_page_by_id(self, request, page_id):
        site_pages = pages_for_site(request.site)
        return site_pages.get(id=page_id)


class DescendantOfFilter(BaseFilterBackend):
    """
    Implements the ?decendant_of filter which limits the set of pages to a
    particular branch of the page tree.
    """
    descendant_of_param = 'descendant_of'
    descendant_of_title = _('All descendants of a page')
    descendant_of_description = _(
        'Id of a page to filters the list of results to contain all descendants (children of children) of that page.'
    )

    def get_root_page(self, request):
        return Page.get_first_root_node()

    def get_page_by_id(self, request, page_id):
        return Page.objects.get(id=page_id)

    def filter_queryset(self, request, queryset, view):
        if self.descendant_of_param in request.GET:
            if getattr(queryset, '_filtered_by_child_of', False):
                raise BadRequestError(
                    "filtering by {} with child_of is not supported".format(self.descendant_of_param)
                )
            try:
                parent_page_id = int(request.GET[self.descendant_of_param])
                assert parent_page_id >= 0

                parent_page = self.get_page_by_id(request, parent_page_id)
            except (ValueError, AssertionError):
                if request.GET[self.descendant_of_param] == 'root':
                    parent_page = self.get_root_page(request)
                else:
                    raise BadRequestError("{} must be a positive integer".format(self.descendant_of_param))
            except Page.DoesNotExist:
                raise BadRequestError("ancestor page doesn't exist")

            queryset = queryset.descendant_of(parent_page)

        return queryset

    def get_schema_fields(self, view):
        assert coreapi is not None, 'coreapi must be installed to use `get_schema_fields()`'
        assert coreschema is not None, 'coreschema must be installed to use `get_schema_fields()`'
        return [
            coreapi.Field(
                name=self.descendant_of_param,
                required=False,
                location='query',
                schema=coreschema.String(
                    title=force_text(self.descendant_of_title),
                    description=force_text(self.descendant_of_description)
                )
            )
        ]


class RestrictedDescendantOfFilter(DescendantOfFilter):
    """
    A restricted version of DecendantOfFilter that only allows pages in the current
    site to be specified.
    """
    def get_root_page(self, request):
        return request.site.root_page

    def get_page_by_id(self, request, page_id):
        site_pages = pages_for_site(request.site)
        return site_pages.get(id=page_id)
