from django.conf import settings
from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework.filters import BaseFilterBackend
from taggit.managers import TaggableManager

from wagtail.models import Locale, Page
from wagtail.search.backends import get_search_backend
from wagtail.search.backends.base import FilterFieldError, OrderByFieldError

from .utils import BadRequestError, parse_boolean


class FieldsFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        """
        This performs field level filtering on the result set
        Eg: ?title=James Joyce
        """
        fields = set(view.get_available_fields(queryset.model, db_fields_only=True))

        # Locale is a database field, but we provide a separate filter for it
        if "locale" in fields:
            fields.remove("locale")

        for field_name, value in request.GET.items():
            if field_name in fields:
                try:
                    field = queryset.model._meta.get_field(field_name)
                except LookupError:
                    field = None

                # Convert value into python
                try:
                    if isinstance(
                        field, (models.BooleanField, models.NullBooleanField)
                    ):
                        value = parse_boolean(value)
                    elif isinstance(field, (models.IntegerField, models.AutoField)):
                        value = int(value)
                    elif isinstance(field, models.ForeignKey):
                        value = field.target_field.get_prep_value(value)
                except ValueError as e:
                    raise BadRequestError(
                        "field filter error. '%s' is not a valid value for %s (%s)"
                        % (value, field_name, str(e))
                    )

                if isinstance(field, TaggableManager):
                    for tag in value.split(","):
                        queryset = queryset.filter(**{field_name + "__name": tag})

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
        if "order" in request.GET:
            order_by = request.GET["order"]

            # Random ordering
            if order_by == "random":
                # Prevent ordering by random with offset
                if "offset" in request.GET:
                    raise BadRequestError(
                        "random ordering with offset is not supported"
                    )

                return queryset.order_by("?")

            # Check if reverse ordering is set
            if order_by.startswith("-"):
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


class SearchFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        """
        This performs a full-text search on the result set
        Eg: ?search=James Joyce
        """
        search_enabled = getattr(settings, "WAGTAILAPI_SEARCH_ENABLED", True)

        if "search" in request.GET:
            if not search_enabled:
                raise BadRequestError("search is disabled")

            # Searching and filtering by tag at the same time is not supported
            if getattr(queryset, "_filtered_by_tag", False):
                raise BadRequestError(
                    "filtering by tag with a search query is not supported"
                )

            search_query = request.GET["search"]
            search_operator = request.GET.get("search_operator", None)
            order_by_relevance = "order" not in request.GET

            sb = get_search_backend()
            try:
                queryset = sb.search(
                    search_query,
                    queryset,
                    operator=search_operator,
                    order_by_relevance=order_by_relevance,
                )
            except FilterFieldError as e:
                raise BadRequestError(
                    "cannot filter by '{}' while searching (field is not indexed)".format(
                        e.field_name
                    )
                )
            except OrderByFieldError as e:
                raise BadRequestError(
                    "cannot order by '{}' while searching (field is not indexed)".format(
                        e.field_name
                    )
                )

        return queryset


class ChildOfFilter(BaseFilterBackend):
    """
    Implements the ?child_of filter used to filter the results to only contain
    pages that are direct children of the specified page.
    """

    def filter_queryset(self, request, queryset, view):
        if "child_of" in request.GET:
            try:
                parent_page_id = int(request.GET["child_of"])
                if parent_page_id < 0:
                    raise ValueError()

                parent_page = view.get_base_queryset().get(id=parent_page_id)
            except ValueError:
                if request.GET["child_of"] == "root":
                    parent_page = view.get_root_page()
                else:
                    raise BadRequestError("child_of must be a positive integer")
            except Page.DoesNotExist:
                raise BadRequestError("parent page doesn't exist")

            queryset = queryset.child_of(parent_page)

            # Save the parent page on the queryset. This is required for the page
            # explorer, which needs to pass the parent page into
            # `construct_explorer_page_queryset` hook functions
            queryset._filtered_by_child_of = parent_page

        return queryset


class AncestorOfFilter(BaseFilterBackend):
    """
    Implements the ?ancestor filter which limits the set of pages to a
    particular branch of the page tree.
    """

    def filter_queryset(self, request, queryset, view):
        if "ancestor_of" in request.GET:
            try:
                descendant_page_id = int(request.GET["ancestor_of"])
                if descendant_page_id < 0:
                    raise ValueError()

                descendant_page = view.get_base_queryset().get(id=descendant_page_id)
            except ValueError:
                raise BadRequestError("ancestor_of must be a positive integer")
            except Page.DoesNotExist:
                raise BadRequestError("descendant page doesn't exist")

            queryset = queryset.ancestor_of(descendant_page)

        return queryset


class DescendantOfFilter(BaseFilterBackend):
    """
    Implements the ?decendant_of filter which limits the set of pages to a
    particular branch of the page tree.
    """

    def filter_queryset(self, request, queryset, view):
        if "descendant_of" in request.GET:
            if hasattr(queryset, "_filtered_by_child_of"):
                raise BadRequestError(
                    "filtering by descendant_of with child_of is not supported"
                )
            try:
                parent_page_id = int(request.GET["descendant_of"])
                if parent_page_id < 0:
                    raise ValueError()

                parent_page = view.get_base_queryset().get(id=parent_page_id)
            except ValueError:
                if request.GET["descendant_of"] == "root":
                    parent_page = view.get_root_page()
                else:
                    raise BadRequestError("descendant_of must be a positive integer")
            except Page.DoesNotExist:
                raise BadRequestError("ancestor page doesn't exist")

            queryset = queryset.descendant_of(parent_page)

        return queryset


class TranslationOfFilter(BaseFilterBackend):
    """
    Implements the ?translation_of filter which limits the set of pages to translations
    of a page.
    """

    def filter_queryset(self, request, queryset, view):
        if "translation_of" in request.GET:
            try:
                page_id = int(request.GET["translation_of"])
                if page_id < 0:
                    raise ValueError()

                page = view.get_base_queryset().get(id=page_id)
            except ValueError:
                if request.GET["translation_of"] == "root":
                    page = view.get_root_page()
                else:
                    raise BadRequestError("translation_of must be a positive integer")
            except Page.DoesNotExist:
                raise BadRequestError("translation_of page doesn't exist")

            _filtered_by_child_of = getattr(queryset, "_filtered_by_child_of", None)

            queryset = queryset.translation_of(page)

            if _filtered_by_child_of:
                queryset._filtered_by_child_of = _filtered_by_child_of

        return queryset


class LocaleFilter(BaseFilterBackend):
    """
    Implements the ?locale filter which limits the set of pages to a
    particular locale.
    """

    def filter_queryset(self, request, queryset, view):
        if "locale" in request.GET:
            _filtered_by_child_of = getattr(queryset, "_filtered_by_child_of", None)

            locale = get_object_or_404(Locale, language_code=request.GET["locale"])
            queryset = queryset.filter(locale=locale)

            if _filtered_by_child_of:
                queryset._filtered_by_child_of = _filtered_by_child_of

        return queryset
