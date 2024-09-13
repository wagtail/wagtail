from django_filters import CharFilter, DateFromToRangeFilter
from django.forms import DateInput
from django.utils.translation import gettext as _

from wagtail.admin.filters import WagtailFilterSet
from wagtail.models import ContentType
from wagtail.contrib.search_promotions.models import Query
from wagtail.admin.views.reports import ReportView
from wagtail.admin.auth import permission_denied
from wagtail.admin.ui.tables import Column
from wagtail.admin.filters import DateRangePickerWidget


class SearchTermsReportFilterSet(WagtailFilterSet):
    query_string = CharFilter(
        label=_("Search term"),
        field_name="query_string",
        lookup_expr="icontains",
    )

    created_at = DateFromToRangeFilter(
        label=_("Searched at"),
        field_name="daily_hits__date",
        widget=DateRangePickerWidget,
    )

    class Meta:
        model = ContentType
        fields = ["query_string", "created_at"]


class SearchTermsReportView(ReportView):
    results_template_name = "wagtailadmin/reports/search_terms_report_results.html"
    page_title = _("Search Terms")
    header_icon = "search"
    filterset_class = SearchTermsReportFilterSet
    index_url_name = "wagtailadmin_reports:search_terms"
    index_results_url_name = "wagtailadmin_reports:search_terms_results"
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