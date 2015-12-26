from django.conf import settings

from rest_framework.filters import BaseFilterBackend

from taggit.managers import _TaggableManager

from wagtail.wagtailcore.models import Page
from wagtail.wagtailsearch.backends import get_search_backend

from .utils import BadRequestError, pages_for_site


class FieldsFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        """
        This performs field level filtering on the result set
        Eg: ?title=James Joyce
        """
        fields = set(view.get_api_fields(queryset.model)).union({'id'})

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


class OrderingFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
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
            if order_by == 'id' or order_by in view.get_api_fields(queryset.model):
                queryset = queryset.order_by(order_by)
            else:
                # Unknown field
                raise BadRequestError("cannot order by '%s' (unknown field)" % order_by)

            # Reverse order
            if reverse_order:
                queryset = queryset.reverse()

        return queryset


class SearchFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
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


class ChildOfFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        if 'child_of' in request.GET:
            try:
                parent_page_id = int(request.GET['child_of'])
                assert parent_page_id >= 0
            except (ValueError, AssertionError):
                raise BadRequestError("child_of must be a positive integer")

            site_pages = pages_for_site(request.site)
            try:
                parent_page = site_pages.get(id=parent_page_id)
                queryset = queryset.child_of(parent_page)
                queryset._filtered_by_child_of = True
                return queryset
            except Page.DoesNotExist:
                raise BadRequestError("parent page doesn't exist")

        return queryset


class DescendantOfFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        if 'descendant_of' in request.GET:
            if getattr(queryset, '_filtered_by_child_of', False):
                raise BadRequestError("filtering by descendant_of with child_of is not supported")
            try:
                ancestor_page_id = int(request.GET['descendant_of'])
                assert ancestor_page_id >= 0
            except (ValueError, AssertionError):
                raise BadRequestError("descendant_of must be a positive integer")

            site_pages = pages_for_site(request.site)
            try:
                ancestor_page = site_pages.get(id=ancestor_page_id)
                return queryset.descendant_of(ancestor_page)
            except Page.DoesNotExist:
                raise BadRequestError("ancestor page doesn't exist")

        return queryset
