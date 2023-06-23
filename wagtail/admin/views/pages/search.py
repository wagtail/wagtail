from typing import Any, Dict

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import InvalidPage, Paginator
from django.http import Http404
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from wagtail.admin.auth import user_has_any_page_permission, user_passes_test
from wagtail.admin.forms.search import SearchForm
from wagtail.models import Page
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


class BaseSearchView(TemplateView):
    @method_decorator(user_passes_test(user_has_any_page_permission))
    def get(self, request):
        pages = self.all_pages = (
            Page.objects.all().prefetch_related("content_type").specific()
        )
        self.show_locale_labels = getattr(settings, "WAGTAIL_I18N_ENABLED", False)
        if self.show_locale_labels:
            pages = pages.select_related("locale")

        self.q = MATCH_ALL
        self.content_types = []
        self.ordering = None

        if "ordering" in request.GET:
            if request.GET["ordering"] in [
                "title",
                "-title",
                "latest_revision_created_at",
                "-latest_revision_created_at",
                "live",
                "-live",
            ]:
                self.ordering = request.GET["ordering"]

                if self.ordering == "title":
                    pages = pages.order_by("title")
                elif self.ordering == "-title":
                    pages = pages.order_by("-title")

                if self.ordering == "latest_revision_created_at":
                    pages = pages.order_by("latest_revision_created_at")
                elif self.ordering == "-latest_revision_created_at":
                    pages = pages.order_by("-latest_revision_created_at")

                if self.ordering == "live":
                    pages = pages.order_by("live")
                elif self.ordering == "-live":
                    pages = pages.order_by("-live")

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

            pages = pages.filter(content_type=self.selected_content_type)
        else:
            self.selected_content_type = None

        if "q" in request.GET:
            self.form = SearchForm(request.GET)
            if self.form.is_valid():
                self.q = self.form.cleaned_data["q"]

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

        else:
            self.form = SearchForm()

        paginator = Paginator(pages, per_page=20)
        try:
            self.pages = paginator.page(request.GET.get("p", 1))
        except InvalidPage:
            raise Http404

        return super().get(request)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "pages": self.pages,
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
        context["search_form"] = self.form
        return context


class SearchResultsView(BaseSearchView):
    template_name = "wagtailadmin/pages/search_results.html"
