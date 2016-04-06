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
        fields = set(view.get_available_fields(queryset.model)).union({'id'})

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
            if order_by == 'id' or order_by in view.get_available_fields(queryset.model):
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
            search_operator = request.GET.get('search_operator', None)

            sb = get_search_backend()
            queryset = sb.search(search_query, queryset, operator=search_operator)

        return queryset


class ChildOfFilter(BaseFilterBackend):
    """
    Implements the ?child_of filter used to filter the results to only contain
    pages that are direct children of the specified page.
    """
    def get_root_page(self, request):
        return Page.get_first_root_node()

    def get_page_by_id(self, request, page_id):
        return Page.objects.get(id=page_id)

    def filter_queryset(self, request, queryset, view):
        if 'child_of' in request.GET:
            try:
                parent_page_id = int(request.GET['child_of'])
                assert parent_page_id >= 0

                parent_page = self.get_page_by_id(request, parent_page_id)
            except (ValueError, AssertionError):
                if request.GET['child_of'] == 'root':
                    parent_page = self.get_root_page(request)
                else:
                    raise BadRequestError("child_of must be a positive integer")
            except Page.DoesNotExist:
                raise BadRequestError("parent page doesn't exist")

            queryset = queryset.child_of(parent_page)
            queryset._filtered_by_child_of = True

        return queryset


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
    def get_root_page(self, request):
        return Page.get_first_root_node()

    def get_page_by_id(self, request, page_id):
        return Page.objects.get(id=page_id)

    def filter_queryset(self, request, queryset, view):
        if 'descendant_of' in request.GET:
            if getattr(queryset, '_filtered_by_child_of', False):
                raise BadRequestError("filtering by descendant_of with child_of is not supported")
            try:
                parent_page_id = int(request.GET['descendant_of'])
                assert parent_page_id >= 0

                parent_page = self.get_page_by_id(request, parent_page_id)
            except (ValueError, AssertionError):
                if request.GET['descendant_of'] == 'root':
                    parent_page = self.get_root_page(request)
                else:
                    raise BadRequestError("descendant_of must be a positive integer")
            except Page.DoesNotExist:
                raise BadRequestError("ancestor page doesn't exist")

            queryset = queryset.descendant_of(parent_page)

        return queryset


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
