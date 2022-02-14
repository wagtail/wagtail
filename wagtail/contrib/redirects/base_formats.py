"""
Copyright (c) Bojan Mihelac and individual contributors.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice,
       this list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright
       notice, this list of conditions and the following disclaimer in the
       documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
# https://raw.githubusercontent.com/django-import-export/django-import-export/main/import_export/formats/base_formats.py
from importlib import import_module

import tablib


class Format:
    def get_title(self):
        return type(self)

    def create_dataset(self, in_stream):
        """
        Create dataset from given string.
        """
        raise NotImplementedError()

    def export_data(self, dataset, **kwargs):
        """
        Returns format representation for given dataset.
        """
        raise NotImplementedError()

    def is_binary(self):
        """
        Returns if this format is binary.
        """
        return True

    def get_read_mode(self):
        """
        Returns mode for opening files.
        """
        return "rb"

    def get_extension(self):
        """
        Returns extension for this format files.
        """
        return ""

    def get_content_type(self):
        # For content types see
        # https://www.iana.org/assignments/media-types/media-types.xhtml
        return "application/octet-stream"

    @classmethod
    def is_available(cls):
        return True

    def can_import(self):
        return False

    def can_export(self):
        return False


class TablibFormat(Format):
    TABLIB_MODULE = None
    CONTENT_TYPE = "application/octet-stream"

    def get_format(self):
        """
        Import and returns tablib module.
        """
        try:
            # Available since tablib 1.0
            from tablib.formats import registry
        except ImportError:
            return import_module(self.TABLIB_MODULE)
        else:
            key = self.TABLIB_MODULE.split(".")[-1].replace("_", "")
            return registry.get_format(key)

    @classmethod
    def is_available(cls):
        try:
            cls().get_format()
        except (tablib.core.UnsupportedFormat, ImportError):
            return False
        return True

    def get_title(self):
        return self.get_format().title

    def create_dataset(self, in_stream, **kwargs):
        return tablib.import_set(in_stream, format=self.get_title())

    def export_data(self, dataset, **kwargs):
        return dataset.export(self.get_title(), **kwargs)

    def get_extension(self):
        return self.get_format().extensions[0]

    def get_content_type(self):
        return self.CONTENT_TYPE

    def can_import(self):
        return hasattr(self.get_format(), "import_set")

    def can_export(self):
        return hasattr(self.get_format(), "export_set")


class TextFormat(TablibFormat):
    def get_read_mode(self):
        return "r"

    def is_binary(self):
        return False


class CSV(TextFormat):
    TABLIB_MODULE = "tablib.formats._csv"
    CONTENT_TYPE = "text/csv"

    def create_dataset(self, in_stream, **kwargs):
        return super().create_dataset(in_stream, **kwargs)


class JSON(TextFormat):
    TABLIB_MODULE = "tablib.formats._json"
    CONTENT_TYPE = "application/json"


class YAML(TextFormat):
    TABLIB_MODULE = "tablib.formats._yaml"
    # See https://stackoverflow.com/questions/332129/yaml-mime-type
    CONTENT_TYPE = "text/yaml"


class TSV(TextFormat):
    TABLIB_MODULE = "tablib.formats._tsv"
    CONTENT_TYPE = "text/tab-separated-values"

    def create_dataset(self, in_stream, **kwargs):
        return super().create_dataset(in_stream, **kwargs)


class ODS(TextFormat):
    TABLIB_MODULE = "tablib.formats._ods"
    CONTENT_TYPE = "application/vnd.oasis.opendocument.spreadsheet"


class HTML(TextFormat):
    TABLIB_MODULE = "tablib.formats._html"
    CONTENT_TYPE = "text/html"


class XLS(TablibFormat):
    TABLIB_MODULE = "tablib.formats._xls"
    CONTENT_TYPE = "application/vnd.ms-excel"

    def create_dataset(self, in_stream):
        """
        Create dataset from first sheet.
        """
        import xlrd

        xls_book = xlrd.open_workbook(file_contents=in_stream)
        dataset = tablib.Dataset()
        sheet = xls_book.sheets()[0]

        dataset.headers = sheet.row_values(0)
        for i in range(1, sheet.nrows):
            dataset.append(sheet.row_values(i))
        return dataset


class XLSX(TablibFormat):
    TABLIB_MODULE = "tablib.formats._xlsx"
    CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def create_dataset(self, in_stream):
        """
        Create dataset from first sheet.
        """
        from io import BytesIO

        import openpyxl

        xlsx_book = openpyxl.load_workbook(BytesIO(in_stream), read_only=True)

        dataset = tablib.Dataset()
        sheet = xlsx_book.active

        # obtain generator
        rows = sheet.rows
        dataset.headers = [cell.value for cell in next(rows)]

        for row in rows:
            row_values = [cell.value for cell in row]
            dataset.append(row_values)
        return dataset


#: These are the default formats for import and export. Whether they can be
#: used or not is depending on their implementation in the tablib library.
DEFAULT_FORMATS = [
    fmt
    for fmt in (
        CSV,
        XLS,
        XLSX,
        TSV,
        ODS,
        JSON,
        YAML,
        HTML,
    )
    if fmt.is_available()
]
