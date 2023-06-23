from typing import Any, Dict

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models.query import QuerySet
from django.http import Http404
from django.views.generic import ListView

from wagtail.admin.forms.search import SearchForm
from wagtail.admin.views.generic.permissions import PermissionCheckedMixin
from wagtail.models import Page
from wagtail.permission_policies.pages import PagePermissionPolicy
from wagtail.search.query import MATCH_ALL
from wagtail.search.utils import parse_query_string


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
    if all_pages is not None:
        all_pages = all_pages.search(query, order_by_relevance=not ordering)
    pages = pages.search(query, order_by_relevance=not ordering)

    return pages, all_pages


class BaseSearchView(PermissionCheckedMixin, ListView):
    permission_policy = PagePermissionPolicy()
    any_permission_required = {
        "add",
        "change",
        "publish",
        "bulk_delete",
        "lock",
        "unlock",
    }
    paginate_by = 20
    page_kwarg = "p"
    context_object_name = "pages"

    def get(self, request):
        self.show_locale_labels = getattr(settings, "WAGTAIL_I18N_ENABLED", False)

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
            except ValueError:
                raise Http404

            try:
                self.selected_content_type = ContentType.objects.get_by_natural_key(
                    app_label, model_name
                )
            except ContentType.DoesNotExist:
                raise Http404

        else:
            self.selected_content_type = None

        self.q = self.request.GET.get("q", "")

        return super().get(request)

    def get_queryset(self) -> QuerySet[Any]:
        pages = self.all_pages = (
            Page.objects.all().prefetch_related("content_type").specific()
        )
        if self.show_locale_labels:
            pages = pages.select_related("locale")

        if self.ordering:
            pages = pages.order_by(self.ordering)

        if self.selected_content_type:
            pages = pages.filter(content_type=self.selected_content_type)

        if self.q:
            # Parse query and filter
            pages, self.all_pages = page_filter_search(
                self.q, pages, self.all_pages, self.ordering
            )

            # Facets
            if pages.supports_facet:
                self.content_types = [
                    (ContentType.objects.get(id=content_type_id), count)
                    for content_type_id, count in self.all_pages.facet(
                        "content_type_id"
                    ).items()
                ]

        return pages

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "all_pages": self.all_pages,
                "query_string": self.q,
                "content_types": self.content_types,
                "selected_content_type": self.selected_content_type,
                "ordering": self.ordering,
                "show_locale_labels": self.show_locale_labels,
            }
        )
        return context


class SearchView(BaseSearchView):
    template_name = "wagtailadmin/pages/search.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["search_form"] = SearchForm(self.request.GET)
        return context


class SearchResultsView(BaseSearchView):
    template_name = "wagtailadmin/pages/search_results.html"
