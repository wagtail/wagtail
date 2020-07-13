import csv
import datetime
from collections import OrderedDict

from django.core.exceptions import FieldDoesNotExist
from django.db.models import Q, Subquery
from django.http import HttpResponse, StreamingHttpResponse
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.list import BaseListView
from xlsxwriter.workbook import Workbook

from wagtail.admin.auth import permission_denied
from wagtail.admin.filters import (
    LockedPagesReportFilterSet, SiteHistoryReportFilterSet, WorkflowReportFilterSet,
    WorkflowTasksReportFilterSet)
from wagtail.core.models import (
    Page, PageLogEntry, Site, TaskState, UserPagePermissionsProxy, WorkflowState)


class Echo:
    """An object that implements just the write method of the file-like interface."""

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value.encode("UTF-8")


def list_to_str(value):
    return force_str(", ".join(value))


class SpreadsheetExportMixin:
    """ A mixin for views, providing spreadsheet export functionality in csv and xlsx formats """

    FORMAT_XLSX = "xlsx"
    FORMAT_CSV = "csv"
    FORMATS = (FORMAT_XLSX, FORMAT_CSV)

    # A list of fields or callables (without arguments) to export from each item in the queryset (dotted paths allowed)
    list_export = []
    # A dictionary of custom preprocessing functions by field and format (expected value would be of the form {field_name: {format: function}})
    # If a valid field preprocessing function is found, any applicable value preprocessing functions will not be used
    custom_field_preprocess = {}
    # A dictionary of preprocessing functions by value class and format
    custom_value_preprocess = {
        (datetime.date, datetime.time): {FORMAT_XLSX: None},
        list: {FORMAT_CSV: list_to_str, FORMAT_XLSX: list_to_str},
    }
    # A dictionary of column heading overrides in the format {field: heading}
    export_headings = {}

    def get_filename(self):
        """ Gets the base filename for the exported spreadsheet, without extensions """
        return "spreadsheet-export"

    def to_row_dict(self, item):
        """ Returns an OrderedDict (in the order given by list_export) of the exportable information for a model instance"""
        row_dict = OrderedDict(
            (field, self.multigetattr(item, field)) for field in self.list_export
        )
        return row_dict

    def multigetattr(self, item, multi_attribute):
        """ Gets the value of a dot-pathed sequence of attributes/callables on a model, calling at each stage if possible """
        current_value = item
        for attribute in multi_attribute.split("."):
            try:
                current_value = current_value()
            except TypeError:
                pass
            current_value = getattr(current_value, attribute)
        try:
            return current_value()
        except TypeError:
            return current_value

    def get_preprocess_function(self, field, value, export_format):
        """ Returns the preprocessing function for a given field name, field value, and export format"""

        # Try to find a field specific function and return it
        format_dict = self.custom_field_preprocess.get(field, {})
        if export_format in format_dict:
            return format_dict[export_format]

        # Otherwise check for a value class specific function
        for value_classes, format_dict in self.custom_value_preprocess.items():
            if isinstance(value, value_classes) and export_format in format_dict:
                return format_dict[export_format]

        # Finally resort to force_str to prevent encoding errors
        return force_str

    def write_xlsx_row(self, worksheet, row_dict, row_number):
        for col_number, (field, value) in enumerate(row_dict.items()):
            preprocess_function = self.get_preprocess_function(
                field, value, self.FORMAT_XLSX
            )
            processed_value = (
                preprocess_function(value) if preprocess_function else value
            )
            worksheet.write(row_number, col_number, processed_value)

    def write_csv_row(self, writer, row_dict):
        processed_row = {}
        for field, value in row_dict.items():
            preprocess_function = self.get_preprocess_function(
                field, value, self.FORMAT_CSV
            )
            processed_value = (
                preprocess_function(value) if preprocess_function else value
            )
            processed_row[field] = processed_value
        return writer.writerow(processed_row)

    def get_heading(self, queryset, field):
        """ Get the heading label for a given field for a spreadsheet generated from queryset """
        heading_override = self.export_headings.get(field)
        if heading_override:
            return force_str(heading_override)
        try:
            return force_str(
                queryset.model._meta.get_field(field).verbose_name.title()
            )
        except (AttributeError, FieldDoesNotExist):
            return force_str(field)

    def stream_csv(self, queryset):
        """ Generate a csv file line by line from queryset, to be used in a StreamingHTTPResponse """
        writer = csv.DictWriter(Echo(), fieldnames=self.list_export)
        yield writer.writerow(
            {field: self.get_heading(queryset, field) for field in self.list_export}
        )

        for item in queryset:
            yield self.write_csv_row(writer, self.to_row_dict(item))

    def write_xlsx(self, queryset, output):
        """ Write an xlsx workbook from a queryset"""
        workbook = Workbook(
            output,
            {
                "in_memory": True,
                "constant_memory": True,
                "remove_timezone": True,
                "default_date_format": "dd/mm/yy hh:mm:ss",
            },
        )
        worksheet = workbook.add_worksheet()

        for col_number, field in enumerate(self.list_export):
            worksheet.write(0, col_number, self.get_heading(queryset, field))

        for row_number, item in enumerate(queryset):
            self.write_xlsx_row(worksheet, self.to_row_dict(item), row_number + 1)

        workbook.close()

    def write_xlsx_response(self, queryset):
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="{}.xlsx"'.format(
            self.get_filename()
        )
        self.write_xlsx(queryset, response)

        return response

    def write_csv_response(self, queryset):
        stream = self.stream_csv(queryset)

        response = StreamingHttpResponse(stream, content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="{}.csv"'.format(
            self.get_filename()
        )
        return response

    def as_spreadsheet(self, queryset, spreadsheet_format):
        """ Return a response with a spreadsheet representing the exported data from queryset, in the format specified"""
        if spreadsheet_format == self.FORMAT_CSV:
            return self.write_csv_response(queryset)
        elif spreadsheet_format == self.FORMAT_XLSX:
            return self.write_xlsx_response(queryset)

    def get_export_url(self, format):
        params = self.request.GET.copy()
        params['export'] = format
        return self.request.path + '?' + params.urlencode()

    @property
    def xlsx_export_url(self):
        return self.get_export_url('xlsx')

    @property
    def csv_export_url(self):
        return self.get_export_url('csv')


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


class LockedPagesView(PageReportView):
    template_name = "wagtailadmin/reports/locked_pages.html"
    title = _("Locked pages")
    header_icon = "locked"
    list_export = PageReportView.list_export + [
        "locked_at",
        "locked_by",
    ]
    filterset_class = LockedPagesReportFilterSet

    def get_filename(self):
        return "locked-pages-report-{}".format(
            datetime.datetime.today().strftime("%Y-%m-%d")
        )

    def get_queryset(self):
        pages = (
            UserPagePermissionsProxy(self.request.user).editable_pages()
            | Page.objects.filter(locked_by=self.request.user)
        ).filter(locked=True)
        self.queryset = pages
        return super().get_queryset()

    def dispatch(self, request, *args, **kwargs):
        if not UserPagePermissionsProxy(request.user).can_remove_locks():
            return permission_denied(request)
        return super().dispatch(request, *args, **kwargs)


class WorkflowView(ReportView):
    template_name = 'wagtailadmin/reports/workflow.html'
    title = _('Workflows')
    header_icon = 'tasks'
    filterset_class = WorkflowReportFilterSet

    export_headings = {
        "page.id": _("Page ID"),
        "page.content_type.model_class._meta.verbose_name.title": _("Page Type"),
        "page.title": _("Page Title"),
        "get_status_display": _("Status"),
        "created_at": _("Started at")
    }
    list_export = [
        "workflow",
        "page.id",
        "page.content_type.model_class._meta.verbose_name.title",
        "page.title",
        "get_status_display",
        "requested_by",
        "created_at",
    ]

    def get_filename(self):
        return "workflow-report-{}".format(
            datetime.datetime.today().strftime("%Y-%m-%d")
        )

    def get_queryset(self):
        pages = UserPagePermissionsProxy(self.request.user).editable_pages()
        return WorkflowState.objects.filter(page__in=pages).order_by('-created_at')


class WorkflowTasksView(ReportView):
    template_name = 'wagtailadmin/reports/workflow_tasks.html'
    title = _('Workflow tasks')
    header_icon = 'thumbtack'
    filterset_class = WorkflowTasksReportFilterSet

    export_headings = {
        "workflow_state.page.id": _("Page ID"),
        "workflow_state.page.content_type.model_class._meta.verbose_name.title": _("Page Type"),
        "workflow_state.page.title": _("Page Title"),
        "get_status_display": _("Status"),
        "workflow_state.requested_by": _("Requested By")
    }
    list_export = [
        "task",
        "workflow_state.page.id",
        "workflow_state.page.content_type.model_class._meta.verbose_name.title",
        "workflow_state.page.title",
        "get_status_display",
        "workflow_state.requested_by",
        "started_at",
        "finished_at",
        "finished_by",
    ]

    def get_filename(self):
        return "workflow-tasks-{}".format(
            datetime.datetime.today().strftime("%Y-%m-%d")
        )

    def get_queryset(self):
        pages = UserPagePermissionsProxy(self.request.user).editable_pages()
        return TaskState.objects.filter(workflow_state__page__in=pages).order_by('-started_at')


class LogEntriesView(ReportView):
    template_name = 'wagtailadmin/reports/site_history.html'
    title = _('Site history')
    header_icon = 'cogs'
    filterset_class = SiteHistoryReportFilterSet

    export_headings = {
        "object_id": _("ID"),
        "title": _("Title"),
        "object_verbose_name": _("Type"),
        "action": _("Action type"),
        "timestamp": _("Date/Time")
    }
    list_export = [
        "object_id",
        "label",
        "object_verbose_name",
        "action",
        "timestamp"
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.custom_field_preprocess['action'] = {
            self.FORMAT_CSV: self.get_action_label, self.FORMAT_XLSX: self.get_action_label
        }

    def get_filename(self):
        return "audit-log-{}".format(
            datetime.datetime.today().strftime("%Y-%m-%d")
        )

    def get_queryset(self):
        q = Q(
            page__in=UserPagePermissionsProxy(self.request.user).explorable_pages().values_list('pk', flat=True)
        )
        root_page_permissions = Site.find_for_request(self.request).root_page.permissions_for_user(self.request.user)
        if (
            self.request.user.is_superuser
            or root_page_permissions.can_add_subpage() or root_page_permissions.can_edit()
        ):
            # Include deleted entries
            q = q | Q(page_id__in=Subquery(
                PageLogEntry.objects.filter(deleted=True).values('page_id')
            ))

        return PageLogEntry.objects.filter(q)

    def get_action_label(self, action):
        from wagtail.admin.log_action_registry import registry as log_action_registry
        return force_str(log_action_registry.get_action_label(action))
