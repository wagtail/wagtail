import csv
import datetime

from xlsxwriter.workbook import Workbook

from collections import OrderedDict

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, FieldDoesNotExist
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
    export_heading_overrides = {}

    def get_filename(self):
        return "spreadsheet-export"

    def to_row_dict(self, item):
        row_dict = OrderedDict((field, self.multigetattr(item, field)) for field in self.list_export)
        return row_dict

    def multigetattr(self, item, multi_attribute):
        current_value = item
        for attribute in multi_attribute.split('.'):
            try:
                current_value = current_value()
            except TypeError:
                pass
            current_value = getattr(current_value, attribute)
        try:
            return current_value()
        except TypeError:
            return current_value
        
    def write_xlsx_row(self, worksheet, row_dict, row_number):
        for col_number, (field, value) in enumerate(row_dict.items()):
            if not isinstance(value, (datetime.date, datetime.time)):
                preprocess_function = self.custom_xlsx_field_preprocess.get(field, force_str)
            else:
                preprocess_function = self.custom_xlsx_field_preprocess.get(field)
            processed_value = preprocess_function(value) if preprocess_function else value
            worksheet.write(row_number, col_number, processed_value)
    
    def write_csv_row(self, writer, row_dict):
        processed_row = {}
        for field, value in row_dict.items():
            preprocess_function = self.custom_csv_field_preprocess.get(field, force_str)
            processed_value = preprocess_function(value) if preprocess_function else value
            processed_row[field] = processed_value
        return writer.writerow(processed_row)

    def get_heading(self, queryset, field):
        heading_override = self.export_heading_overrides.get(field)
        if heading_override:
            return force_str(heading_override)
        try:
            return force_str(queryset.first()._meta.get_field(field).verbose_name.title())
        except (AttributeError, FieldDoesNotExist):
            return force_str(field)

    def stream_csv(self, queryset):
        writer = csv.DictWriter(Echo(), fieldnames=self.list_export)
        yield writer.writerow({field: self.get_heading(queryset, field) for field in self.list_export})

        for item in queryset:
            yield self.write_csv_row(writer, self.to_row_dict(item))
    
    def write_xlsx(self, queryset, output):
        workbook = Workbook(output, {'in_memory': True, 'constant_memory': True, 'remove_timezone': True, 'default_date_format': 'dd/mm/yy hh:mm:ss'})
        worksheet = workbook.add_worksheet()

        for col_number, field in enumerate(self.list_export):
            worksheet.write(0, col_number, self.get_heading(queryset, field))

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
    list_export = []

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
    export_heading_overrides = {'latest_revision_created_at': _("Updated"), 'status_string': _("Status"), 'content_type.model_class._meta.verbose_name.title': _("Type")}
    list_export = ['title', 'latest_revision_created_at', 'status_string', 'content_type.model_class._meta.verbose_name.title', 'locked_at', 'locked_by']

    def get_queryset(self):
        pages = UserPagePermissionsProxy(self.request.user).editable_pages().filter(locked=True)
        self.queryset = pages
        return super().get_queryset()

    def dispatch(self, request, *args, **kwargs):
        if not UserPagePermissionsProxy(request.user).can_remove_locks():
            return permission_denied(request)
        return super().dispatch(request, *args, **kwargs)
