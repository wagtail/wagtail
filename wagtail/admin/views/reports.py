import csv
import datetime
from collections import OrderedDict

from django.core.exceptions import FieldDoesNotExist
from django.http import HttpResponse, StreamingHttpResponse
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.list import BaseListView
from xlsxwriter.workbook import Workbook

from wagtail.admin.auth import permission_denied
from wagtail.core.models import UserPagePermissionsProxy


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


class ReportView(SpreadsheetExportMixin, TemplateResponseMixin, BaseListView):
    header_icon = ""
    page_kwarg = "p"
    template_name = "wagtailadmin/reports/base_report.html"
    title = ""
    paginate_by = 50

    def dispatch(self, request, *args, **kwargs):
        self.is_export = self.request.GET.get("export") in self.FORMATS
        if self.is_export:
            self.paginate_by = None
            return self.as_spreadsheet(self.get_queryset(), self.request.GET.get("export"))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, object_list=None, **kwargs):
        context = super().get_context_data(*args, object_list=object_list, **kwargs)
        context["title"] = self.title
        context["header_icon"] = self.header_icon
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
    title = _("Locked Pages")
    header_icon = "locked"
    list_export = PageReportView.list_export + [
        "locked_at",
        "locked_by",
    ]

    def get_filename(self):
        return "locked-pages-report-{}".format(
            datetime.datetime.today().strftime("%Y-%m-%d")
        )

    def get_queryset(self):
        pages = (
            UserPagePermissionsProxy(self.request.user)
            .editable_pages()
            .filter(locked=True)
        )
        self.queryset = pages
        return super().get_queryset()

    def dispatch(self, request, *args, **kwargs):
        if not UserPagePermissionsProxy(request.user).can_remove_locks():
            return permission_denied(request)
        return super().dispatch(request, *args, **kwargs)
