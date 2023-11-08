import csv
from io import BytesIO, StringIO

import openpyxl


class Dataset(list):
    def __init__(self, rows=(), headers=None):
        super().__init__(rows)
        self.headers = headers or (self.pop(0) if len(self) > 0 else [])

    def __str__(self):
        """Print a table"""
        result = [[]]
        widths = []

        for col in self.headers:
            value = str(col) if col is not None else ""
            result[0].append(value)
            widths.append(len(value) + 1)

        for row in self:
            result.append([])
            for idx, col in enumerate(row):
                value = str(col) if col is not None else ""
                result[-1].append(value)
                widths[idx] = max(widths[idx], len(value) + 1)

        row_formatter = (
            "| ".join(f"{{{idx}:{width}}}" for idx, width in enumerate(widths))
        ).format

        return "\n".join(row_formatter(*row) for row in result)


class CSV:
    def is_binary(self):
        return False

    def get_read_mode(self):
        return "r"

    def create_dataset(self, data, delimiter=","):
        """
        Create dataset from csv data.
        """
        return Dataset(csv.reader(StringIO(data), delimiter=delimiter))


class TSV(CSV):
    def create_dataset(self, data):
        """
        Create dataset from tsv data.
        """
        return super().create_dataset(data, delimiter="\t")


class XLSX:
    def is_binary(self):
        return True

    def get_read_mode(self):
        return "rb"

    def create_dataset(self, data):
        """
        Create dataset from the first sheet of a xlsx workbook.
        """
        workbook = openpyxl.load_workbook(BytesIO(data), read_only=True, data_only=True)
        sheet = workbook.worksheets[0]
        try:
            return Dataset(tuple(cell.value for cell in row) for row in sheet.rows)
        finally:
            workbook.close()


DEFAULT_FORMATS = [
    CSV,
    XLSX,
    TSV,
]
