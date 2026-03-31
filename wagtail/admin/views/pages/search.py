import logging
from typing import Any

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models.query import QuerySet
from django.http import Http404
from django.utils.functional import classproperty
from django.utils.translation import gettext_lazy as _
from modelsearch.backends.database.postgres.postgres import PostgresSearchBackend
from modelsearch.backends.elasticsearchbase import ElasticsearchBaseSearchBackend

from wagtail.admin.ui.tables.pages import (
    NavigateToChildrenColumn,
)
from wagtail.admin.views.generic.base import BaseListingView
from wagtail.admin.views.generic.permissions import PermissionCheckedMixin
from wagtail.admin.views.pages.listing import PageListingMixin
from wagtail.models import Page
from wagtail.permissions import page_permission_policy
from wagtail.search.backends import get_search_backend
from wagtail.search.query import MATCH_ALL, Fuzzy
from wagtail.search.utils import parse_query_string

logger = logging.getLogger(__name__)

_FUZZY_SUPPORTED_BACKENDS = (PostgresSearchBackend, ElasticsearchBaseSearchBackend)


def build_fuzzy_query(q):
    """
    Returns a Fuzzy query for the given string if WAGTAIL_FUZZY_SEARCH is
    enabled and the active search backend supports it, otherwise returns None.
    """
    if not getattr(settings, "WAGTAIL_FUZZY_SEARCH", False):
        return None

    if not isinstance(get_search_backend(), _FUZZY_SUPPORTED_BACKENDS):
        logger.warning(
            "WAGTAIL_FUZZY_SEARCH is enabled but the active search backend does not "
            "support fuzzy search. Falling back to autocomplete. Use PostgreSQL or "
            "Elasticsearch/OpenSearch to enable fuzzy search."
        )
        return None

    unaccent = getattr(settings, "WAGTAIL_FUZZY_SEARCH_UNACCENT", False)
    return Fuzzy(q, unaccent=unaccent)


def page_filter_search(q, pages, all_pages=None, ordering=None):
    # Parse query
    filters, query = parse_query_string(q, operator="and", zero_terms=MATCH_ALL)

    # Live filter
    live_filter = filters.get("live") or filters.get("published")
    live_filter = live_filter and live_filter.lower()

    if live_filter in ["yes", "true"]:
        if all_pages is not None:
            all_pages = all_pages.filter(live=True)
        pages = pages.filter(live=True)
    elif live_filter in ["no", "false"]:
        if all_pages is not None:
            all_pages = all_pages.filter(live=False)
        pages = pages.filter(live=False)

    # Search
    fuzzy_query = build_fuzzy_query(q) if q else None
    if fuzzy_query:
        if all_pages is not None:
            all_pages = all_pages.search(fuzzy_query, order_by_relevance=not ordering)
        pages = pages.search(fuzzy_query, order_by_relevance=not ordering)
    else:
        if all_pages is not None:
            all_pages = all_pages.autocomplete(query, order_by_relevance=not ordering)
        pages = pages.autocomplete(query, order_by_relevance=not ordering)

    return pages, all_pages


class SearchView(PageListingMixin, PermissionCheckedMixin, BaseListingView):
    permission_policy = page_permission_policy
    any_permission_required = {
        "add",
        "change",
        "publish",
        "bulk_delete",
        "lock",
        "unlock",
    }
    paginate_by = 20
    page_title = _("Search")
    header_icon = "search"
    index_url_name = "wagtailadmin_pages:search"
    index_results_url_name = "wagtailadmin_pages:search_results"
    # We override get_queryset here that has a custom search implementation
    is_searchable = True
    # The queryset always gets passed to the search backend even if
    # the search query is empty, so we are always "searching"
    is_searching = True
    # This view has its own filtering mechanism that doesn't use django-filter
    filterset_class = None
    template_name = "wagtailadmin/pages/search.html"
    results_template_name = "wagtailadmin/pages/search_results.html"

    @classproperty
    def columns(cls):
        columns = PageListingMixin.columns.copy()
        columns.append(NavigateToChildrenColumn("navigate", width="10%"))
        return columns

    def get(self, request):
        self.content_types = []
        self.ordering = None

        if "ordering" in request.GET and request.GET["ordering"] in [
            "title",
            "-title",
            "latest_revision_created_at",
            "-latest_revision_created_at",
            "live",
            "-live",
        ]:
            self.ordering = request.GET["ordering"]

        if "content_type" in request.GET:
            try:
                app_label, model_name = request.GET["content_type"].split(".")
            except ValueError as e:
                raise Http404 from e

            try:
                self.selected_content_type = ContentType.objects.get_by_natural_key(
                    app_label, model_name
                )
            except ContentType.DoesNotExist as e:
                raise Http404 from e

        else:
            self.selected_content_type = None

        return super().get(request)

    def get_queryset(self) -> QuerySet[Any]:
        pages = self.all_pages = Page.objects.all().filter(
            pk__in=page_permission_policy.explorable_instances(
                self.request.user
            ).values_list("pk", flat=True)
        )
        if self.show_locale_labels:
            pages = pages.select_related("locale")

        if self.ordering:
            pages = pages.order_by(self.ordering)

        if self.selected_content_type:
            pages = pages.filter(content_type=self.selected_content_type)

        pages = self.annotate_queryset(pages)

        # Parse query and filter
        pages, self.all_pages = page_filter_search(
            self.search_query,
            pages,
            self.all_pages,
            self.ordering,
        )

        # Facets
        if pages.supports_facet:
            self.content_types = [
                (ContentType.objects.get_for_id(content_type_id), count)
                for content_type_id, count in self.all_pages.facet(
                    "content_type_id"
                ).items()
            ]

        return pages

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "all_pages": self.all_pages,
                "content_types": self.content_types,
                "selected_content_type": self.selected_content_type,
            }
        )
        return context
