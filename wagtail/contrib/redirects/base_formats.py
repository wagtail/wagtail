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
from io import BytesIO

import openpyxl
import tablib


class CSV:
    def is_binary(self):
        return False

    def get_read_mode(self):
        return "r"

    def create_dataset(self, in_stream):
        return tablib.import_set(in_stream, format="csv")


class TSV(CSV):
    def create_dataset(self, in_stream):
        return tablib.import_set(in_stream, format="tsv")


class XLSX:
    def is_binary(self):
        return True

    def get_read_mode(self):
        return "rb"

    def create_dataset(self, in_stream):
        """
        Create dataset from first sheet.
        """
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


DEFAULT_FORMATS = [
    CSV,
    XLSX,
    TSV,
]
