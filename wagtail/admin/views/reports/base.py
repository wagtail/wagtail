from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.list import BaseListView

from wagtail.admin.views.mixins import SpreadsheetExportMixin


class ReportView(SpreadsheetExportMixin, TemplateResponseMixin, BaseListView):
    header_icon = ""
    page_kwarg = "p"
    template_name = "wagtailadmin/reports/base_report.html"
    title = ""
    paginate_by = 50
    filterset_class = None

    def filter_queryset(self, queryset):
        filters = None

        if self.filterset_class:
            filters = self.filterset_class(self.request.GET, queryset=queryset, request=self.request)
            queryset = filters.qs

        return filters, queryset

    def dispatch(self, request, *args, **kwargs):
        self.is_export = self.request.GET.get("export") in self.FORMATS
        if self.is_export:
            self.paginate_by = None
            return self.as_spreadsheet(self.filter_queryset(self.get_queryset())[1], self.request.GET.get("export"))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, object_list=None, **kwargs):
        queryset = object_list if object_list is not None else self.object_list
        filters, queryset = self.filter_queryset(queryset)

        context = super().get_context_data(*args, object_list=queryset, **kwargs)
        context["title"] = self.title
        context["header_icon"] = self.header_icon
        context["filters"] = filters
        return context


class PageReportView(ReportView):
    template_name = "wagtailadmin/reports/base_page_report.html"
    export_headings = {
        "latest_revision_created_at": _("Updated"),
        "status_string": _("Status"),
        "content_type.model_class._meta.verbose_name.title": _("Type"),
    }
    list_export = [
        "title",
        "latest_revision_created_at",
        "status_string",
        "content_type.model_class._meta.verbose_name.title",
    ]
