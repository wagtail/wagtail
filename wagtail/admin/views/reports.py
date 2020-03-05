import csv
from xlsxwriter.workbook import Workbook

from collections import OrderedDict

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse, StreamingHttpResponse
from django.utils.encoding import force_str
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.list import BaseListView

from wagtail.admin.auth import permission_denied
from wagtail.core.models import UserPagePermissionsProxy


class Echo:
    """An object that implements just the write method of the file-like interface."""

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value.encode('UTF-8')


class SpreadsheetExportMixin:
    list_export = []
    custom_xlsx_field_preprocess = {}
    custom_csv_field_preprocess = {}

    def get_filename(self):
        return "spreadsheet-export"

    def to_row_dict(self, item):
        row_dict = OrderedDict((field, getattr(item, field)) for field in self.list_export)
        return row_dict

    def write_xlsx_row(self, worksheet, row_dict, row_number):
        for col_number, (field, value) in enumerate(row_dict.items()):
            preprocess_function = self.custom_xlsx_field_preprocess.get(field, force_str)
            processed_value = preprocess_function(value) if preprocess_function else value
            worksheet.write(row_number, col_number, processed_value)
    
    def write_csv_row(self, writer, row_dict):
        processed_row = {}
        for field, value in row_dict.items():
            preprocess_function = self.custom_csv_field_preprocess.get(field, force_str)
            processed_value = preprocess_function(value) if preprocess_function else value
            processed_row[field] = processed_value
        return writer.writerow(processed_row)

    def get_heading(self, field):
        return force_str(field)

    def stream_csv(self, queryset):
        writer = csv.DictWriter(Echo(), fieldnames=self.list_export)
        yield writer.writerow({field: self.get_heading(field) for field in self.list_export})

        for item in queryset:
            yield self.write_csv_row(writer, self.to_row_dict(item))
    
    def write_xlsx(self, queryset, output):
        workbook = Workbook(output, {'in_memory': True, 'constant_memory': True})
        worksheet = workbook.add_worksheet()

        for col_number, field in enumerate(self.list_export):
            worksheet.write(0, col_number, self.get_heading(field))

        for row_number, item in enumerate(queryset):
            self.write_xlsx_row(worksheet, self.to_row_dict(item), row_number + 1)

        workbook.close()

    def write_xlsx_response(self, queryset):
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response['Content-Disposition'] = 'attachment; filename="{}.xlsx"'.format(self.get_filename())
        self.write_xlsx(queryset, response)

        return response

    def write_csv_response(self, queryset):
        stream = self.stream_csv(queryset)

        response = StreamingHttpResponse(stream, content_type="text/csv")
        response['Content-Disposition'] = 'attachment; filename="{}.csv"'.format(self.get_filename())
        return response

    def as_spreadsheet(self, queryset):
        spreadsheet_format = getattr(settings, 'WAGTAIL_SPREADSHEET_EXPORT_FORMAT', 'xlsx') 
        if spreadsheet_format == 'csv':
            return self.write_csv_response(queryset)
        elif spreadsheet_format == 'xlsx':
            return self.write_xlsx_response(queryset)
        else:
            raise ImproperlyConfigured(_("WAGTAIL_SPREADSHEET_EXPORT_FORMAT is set to an unrecognised format. Valid options are: 'csv', 'xlsx'"))


class ReportView(SpreadsheetExportMixin, TemplateResponseMixin, BaseListView):
    header_icon = ''
    page_kwarg = 'p'
    template_name = None
    title = ''
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        self.is_export = (self.request.GET.get('action') == 'export')
        if self.is_export:
            self.paginate_by = None
            return self.as_spreadsheet(self.get_queryset())
        return super().dispatch(request, *args, **kwargs)
        

    def get_context_data(self, *args, object_list=None, **kwargs):
        context = super().get_context_data(*args, object_list=object_list, **kwargs)
        context['title'] = self.title
        context['header_icon'] = self.header_icon
        return context


class LockedPagesView(ReportView):
    template_name = 'wagtailadmin/reports/locked_pages.html'
    title = _('Locked Pages')
    header_icon = 'locked'
    list_export = ['title']

    def get_queryset(self):
        pages = UserPagePermissionsProxy(self.request.user).editable_pages().filter(locked=True)
        self.queryset = pages
        return super().get_queryset()

    def dispatch(self, request, *args, **kwargs):
        if not UserPagePermissionsProxy(request.user).can_remove_locks():
            return permission_denied(request)
        return super().dispatch(request, *args, **kwargs)
