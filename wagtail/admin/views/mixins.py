import csv
import datetime
from collections import OrderedDict
from functools import partial
from io import BytesIO

from django.contrib.admin.utils import label_for_field
from django.core.exceptions import FieldDoesNotExist
from django.http import FileResponse, StreamingHttpResponse
from django.utils import timezone
from django.utils.dateformat import Formatter
from django.utils.encoding import force_str
from django.utils.formats import get_format
from django.utils.functional import cached_property
from django.utils.text import capfirst
from django.utils.translation import gettext as _

from wagtail.admin.widgets.button import Button
from wagtail.coreutils import multigetattr


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
        datetime.datetime: {
            FORMAT_XLSX: lambda value: (
                value
                if timezone.is_naive(value)
                else timezone.make_naive(value, datetime.timezone.utc)
            )
        },
        (datetime.date, datetime.time): {FORMAT_XLSX: None},
        list: {FORMAT_CSV: list_to_str, FORMAT_XLSX: list_to_str},
    }
    # A dictionary of column heading overrides in the format {field: heading}
    export_headings = {}

    export_buttons_template_name = "wagtailadmin/shared/export_buttons.html"

    export_filename = "spreadsheet-export"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.is_export = request.GET.get("export") in self.FORMATS

    def get_paginate_by(self, queryset):
        if self.is_export:
            return None
        return super().get_paginate_by(queryset)

    def get_filename(self):
        """Gets the base filename for the exported spreadsheet, without extensions"""
        return self.export_filename

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
        return partial(force_str, strings_only=True)

    def preprocess_field_value(self, field, value, export_format):
        """Preprocesses a field value before writing it to the spreadsheet"""
        preprocess_function = self.get_preprocess_function(field, value, export_format)
        if preprocess_function is not None:
            return preprocess_function(value)
        else:
            return value

    def generate_xlsx_row(self, worksheet, row_dict, date_format=None):
        """Generate cells to append to the worksheet"""
        from openpyxl.cell import WriteOnlyCell

        for field, value in row_dict.items():
            cell = WriteOnlyCell(
                worksheet, self.preprocess_field_value(field, value, self.FORMAT_XLSX)
            )
            if date_format and isinstance(value, datetime.datetime):
                cell.number_format = date_format
            yield cell

    def write_csv_row(self, writer, row_dict):
        return writer.writerow(
            {
                field: self.preprocess_field_value(field, value, self.FORMAT_CSV)
                for field, value in row_dict.items()
            }
        )

    def get_heading(self, queryset, field):
        """Get the heading label for a given field for a spreadsheet generated from queryset"""
        heading_override = self.export_headings.get(field)
        if heading_override:
            return force_str(heading_override)
        try:
            return capfirst(force_str(label_for_field(field, queryset.model)))
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
        from openpyxl import Workbook

        workbook = Workbook(write_only=True, iso_dates=True)

        worksheet = workbook.create_sheet(title="Sheet1")
        worksheet.append(
            self.get_heading(queryset, field) for field in self.list_export
        )

        date_format = ExcelDateFormatter().get()
        for item in queryset:
            worksheet.append(
                self.generate_xlsx_row(
                    worksheet, self.to_row_dict(item), date_format=date_format
                )
            )

        workbook.save(output)

    def write_xlsx_response(self, queryset):
        """Write an xlsx file from a queryset and return a FileResponse"""
        output = BytesIO()
        self.write_xlsx(queryset, output)
        output.seek(0)

        return FileResponse(
            output,
            as_attachment=True,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"{self.get_filename()}.xlsx",
        )

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

    @cached_property
    def show_export_buttons(self):
        return bool(self.list_export)

    @cached_property
    def header_more_buttons(self):
        buttons = super().header_more_buttons.copy()
        if self.show_export_buttons:
            buttons.append(
                Button(
                    _("Download XLSX"),
                    url=self.xlsx_export_url,
                    icon_name="download",
                    priority=90,
                )
            )
            buttons.append(
                Button(
                    _("Download CSV"),
                    url=self.csv_export_url,
                    icon_name="download",
                    priority=100,
                )
            )

        return buttons
