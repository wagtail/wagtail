import csv
import datetime
from collections import OrderedDict

from django.core.exceptions import FieldDoesNotExist
from django.http import HttpResponse, StreamingHttpResponse
from django.utils.dateformat import Formatter
from django.utils.encoding import force_str
from django.utils.formats import get_format
from django.utils.translation import gettext as _
from xlsxwriter.workbook import Workbook

from wagtail.admin.forms.search import SearchForm
from wagtail.coreutils import multigetattr
from wagtail.search.backends import get_search_backend
from wagtail.search.index import class_is_indexed


class SearchableListMixin:
    search_box_placeholder = _("Search")
    search_fields = None

    def get_search_form(self):
        return SearchForm(
            self.request.GET if self.request.GET.get("q") else None,
            placeholder=self.search_box_placeholder,
        )

    def get_queryset(self):
        queryset = super().get_queryset()
        search_form = self.get_search_form()

        if search_form.is_valid():
            q = search_form.cleaned_data["q"]

            if class_is_indexed(queryset.model):
                search_backend = get_search_backend()
                queryset = search_backend.search(q, queryset, fields=self.search_fields)
            else:
                filters = {
                    field + "__icontains": q for field in self.search_fields or []
                }

                queryset = queryset.filter(**filters)

        return queryset

    def get_context_data(self, **kwargs):
        if "search_form" not in kwargs:
            kwargs["search_form"] = self.get_search_form()
            kwargs["is_searching"] = bool(self.request.GET.get("q"))

        return super().get_context_data(**kwargs)


class Echo:
    """An object that implements just the write method of the file-like interface."""

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value.encode("UTF-8")


def list_to_str(value):
    return force_str(", ".join(value))


class ExcelDateFormatter(Formatter):
    data = None

    # From: https://docs.djangoproject.com/en/stable/ref/templates/builtins/#date
    # To: https://support.microsoft.com/en-us/office/format-numbers-as-dates-or-times-418bd3fe-0577-47c8-8caa-b4d30c528309#bm2
    _formats = {
        # Day of the month, 2 digits with leading zeros.
        "d": "dd",
        # Day of the month without leading zeros.
        "j": "d",
        # Day of the week, textual, 3 letters.
        "D": "ddd",
        # Day of the week, textual, full.
        "l": "dddd",
        # English ordinal suffix for the day of the month, 2 characters.
        "S": "",  # Not supported in Excel
        # Day of the week, digits without leading zeros.
        "w": "",  # Not supported in Excel
        # Day of the year.
        "z": "",  # Not supported in Excel
        # ISO-8601 week number of year, with weeks starting on Monday.
        "W": "",  # Not supported in Excel
        # Month, 2 digits with leading zeros.
        "m": "mm",
        # Month without leading zeros.
        "n": "m",
        # Month, textual, 3 letters.
        "M": "mmm",
        # Month, textual, 3 letters, lowercase. (Not supported in Excel)
        "b": "mmm",
        # Month, locale specific alternative representation usually used for long date representation.
        "E": "mmmm",  # Not supported in Excel
        # Month, textual, full.
        "F": "mmmm",
        # Month abbreviation in Associated Press style. Proprietary extension.
        "N": "mmm.",  # Approximation, wrong for May
        # Number of days in the given month.
        "t": "",  # Not supported in Excel
        # Year, 2 digits with leading zeros.
        "y": "yy",
        # Year, 4 digits with leading zeros.
        "Y": "yyyy",
        # Whether it's a leap year.
        "L": "",  # Not supported in Excel
        # ISO-8601 week-numbering year.
        "o": "yyyy",  # Approximation, same as Y
        # Hour, 12-hour format without leading zeros.
        "g": "h",  # Only works when combined with AM/PM, 24-hour format is used otherwise
        # Hour, 24-hour format without leading zeros.
        "G": "hH",
        # Hour, 12-hour format with leading zeros.
        "h": "hh",  # Only works when combined with AM/PM, 24-hour format is used otherwise
        # Hour, 24-hour format with leading zeros.
        "H": "hh",
        # Minutes.
        "i": "mm",
        # Seconds.
        "s": "ss",
        # Microseconds.
        "u": ".00",  # Only works when combined with ss
        # 'a.m.' or 'p.m.'.
        "a": "AM/PM",  # Approximation, uses AM/PM and only works when combined with h/hh
        # AM/PM.
        "A": "AM/PM",  # Only works when combined with h/hh
        # Time, in 12-hour hours and minutes, with minutes left off if they’re zero.
        "f": "h:mm",  # Approximation, uses 24-hour format and minutes are never left off
        # Time, in 12-hour hours, minutes and ‘a.m.’/’p.m.’, with minutes left off if they’re zero and the special-case strings ‘midnight’ and ‘noon’ if appropriate.
        "P": "h:mm AM/PM",  # Approximation, minutes are never left off, no special case strings
        # Timezone name.
        "e": "",  # Not supported in Excel
        # Daylight saving time, whether it’s in effect or not.
        "I": "",  # Not supported in Excel
        # Difference to Greenwich time in hours.
        "O": "",  # Not supported in Excel
        # Time zone of this machine.
        "T": "",  # Not supported in Excel
        # Timezone offset in seconds.
        "Z": "",  # Not supported in Excel
        # ISO 8601 format.
        "c": "yyyy-mm-ddThh:mm:ss.00",
        # RFC 5322 formatted date.
        "r": "ddd, d mmm yyyy hh:mm:ss",
        # Seconds since the Unix epoch.
        "U": "",  # Not supported in Excel
    }

    def get(self):
        format = get_format("SHORT_DATETIME_FORMAT")
        return self.format(format)

    def __getattr__(self, name):
        if name in self._formats:
            return lambda: self._formats[name]
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )


class SpreadsheetExportMixin:
    """A mixin for views, providing spreadsheet export functionality in csv and xlsx formats"""

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
        """Gets the base filename for the exported spreadsheet, without extensions"""
        return "spreadsheet-export"

    def to_row_dict(self, item):
        """Returns an OrderedDict (in the order given by list_export) of the exportable information for a model instance"""
        row_dict = OrderedDict(
            (field, multigetattr(item, field)) for field in self.list_export
        )
        return row_dict

    def get_preprocess_function(self, field, value, export_format):
        """Returns the preprocessing function for a given field name, field value, and export format"""

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
        """Get the heading label for a given field for a spreadsheet generated from queryset"""
        heading_override = self.export_headings.get(field)
        if heading_override:
            return force_str(heading_override)
        try:
            return force_str(queryset.model._meta.get_field(field).verbose_name.title())
        except (AttributeError, FieldDoesNotExist):
            return force_str(field)

    def stream_csv(self, queryset):
        """Generate a csv file line by line from queryset, to be used in a StreamingHTTPResponse"""
        writer = csv.DictWriter(Echo(), fieldnames=self.list_export)
        yield writer.writerow(
            {field: self.get_heading(queryset, field) for field in self.list_export}
        )

        for item in queryset:
            yield self.write_csv_row(writer, self.to_row_dict(item))

    def write_xlsx(self, queryset, output):
        """Write an xlsx workbook from a queryset"""
        workbook = Workbook(
            output,
            {
                "in_memory": True,
                "constant_memory": True,
                "remove_timezone": True,
                "default_date_format": ExcelDateFormatter().get(),
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
        """Return a response with a spreadsheet representing the exported data from queryset, in the format specified"""
        if spreadsheet_format == self.FORMAT_CSV:
            return self.write_csv_response(queryset)
        elif spreadsheet_format == self.FORMAT_XLSX:
            return self.write_xlsx_response(queryset)

    def get_export_url(self, format):
        params = self.request.GET.copy()
        params["export"] = format
        return self.request.path + "?" + params.urlencode()

    @property
    def xlsx_export_url(self):
        return self.get_export_url("xlsx")

    @property
    def csv_export_url(self):
        return self.get_export_url("csv")
