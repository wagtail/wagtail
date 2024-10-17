from django.utils.translation import gettext as _
from django_filters import CharFilter, DateFromToRangeFilter

from wagtail.admin.auth import permission_denied
from wagtail.admin.filters import DateRangePickerWidget, WagtailFilterSet
from wagtail.admin.ui.tables import Column
from wagtail.admin.views.reports import ReportView
from wagtail.contrib.search_promotions.models import Query
from wagtail.models import ContentType


class SearchTermsReportFilterSet(WagtailFilterSet):
    query_string = CharFilter(
        label=_("Search term"),
        field_name="query_string",
        lookup_expr="icontains",
    )

    created_at = DateFromToRangeFilter(
        label=_("Date"),
        field_name="daily_hits__date",
        widget=DateRangePickerWidget,
    )

    class Meta:
        model = ContentType
        fields = ["query_string", "created_at"]


class SearchTermsReportView(ReportView):
    results_template_name = "wagtailsearchpromotions/search_terms_report_results.html"
    page_title = _("Search Terms")
    header_icon = "search"
    filterset_class = SearchTermsReportFilterSet
    index_url_name = "wagtailsearchpromotions:search_terms"
    index_results_url_name = "wagtailsearchpromotions:search_terms_results"
    columns = [
        Column("query_string", label=_("Search term(s)")),
        Column("_hits", label=_("Views")),
    ]
    export_headings = {
        "query_string": _("Search term(s)"),
        "_hits": _("Views"),
    }
    list_export = [
        "query_string",
        "_hits",
    ]

    def get_queryset(self):
        qs = Query.get_most_popular()

        filterset = self.filterset_class(self.request.GET, queryset=qs)
        return filterset.qs

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_superuser:
            return permission_denied(request)
        return super().dispatch(request, *args, **kwargs)
