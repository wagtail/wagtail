from django.core.exceptions import ValidationError
from django.forms.utils import ErrorList
from django.test import TestCase

from wagtail import blocks
from wagtail.blocks.base import get_error_json_data
from wagtail.blocks.struct_block import StructBlockValidationError
from wagtail.contrib.typed_table_block.blocks import (
    TypedTable,
    TypedTableBlock,
    TypedTableBlockValidationError,
)


class CountryChoiceBlock(blocks.ChoiceBlock):
    """A ChoiceBlock with a custom rendering, to check that block rendering is honoured"""

    def render_basic(self, value, context=None):
        return value.upper() if value else value


class TestTableBlock(TestCase):
    def setUp(self):
        self.block = TypedTableBlock(
            [
                ("text", blocks.CharBlock()),
                (
                    "country",
                    CountryChoiceBlock(
                        choices=[
                            ("be", "Belgium"),
                            ("fr", "France"),
                            ("nl", "Netherlands"),
                        ]
                    ),
                ),
            ]
        )

        self.form_data = {
            "table-column-count": "2",
            "table-row-count": "3",
            "table-column-0-type": "country",
            "table-column-0-order": "0",
            "table-column-0-deleted": "",
            "table-column-0-heading": "Country",
            "table-column-1-type": "text",
            "table-column-1-order": "1",
            "table-column-1-deleted": "",
            "table-column-1-heading": "Description",
            "table-row-0-order": "1",
            "table-row-0-deleted": "",
            "table-cell-0-0": "fr",
            "table-cell-0-1": "A large country with baguettes",
            "table-row-1-order": "0",
            "table-row-1-deleted": "",
            "table-cell-1-0": "nl",
            "table-cell-1-1": "A small country with stroopwafels",
            "table-row-2-order": "2",
            "table-row-2-deleted": "1",
            "table-cell-2-0": "be",
            "table-cell-2-1": "A small country with sprouts",
        }

        self.db_data = {
            "columns": [
                {"type": "country", "heading": "Country"},
                {"type": "text", "heading": "Description"},
            ],
            "rows": [
                {"values": ["nl", "A small country with stroopwafels"]},
                {"values": ["fr", "A large country with baguettes"]},
            ],
        }

    def test_value_from_datadict(self):
        """
        Test that we can turn posted form data into a TypedTable instance,
        accounting for row reordering and deleted rows.
        """
        table = self.block.value_from_datadict(self.form_data, {}, "table")

        self.assertIsInstance(table, TypedTable)
        self.assertEqual(len(table.columns), 2)
        self.assertEqual(table.columns[0]["heading"], "Country")
        self.assertEqual(table.columns[1]["heading"], "Description")
        rows = list(table.rows)
        self.assertEqual(len(rows), 2)
        self.assertEqual(
            [block.value for block in rows[0]],
            ["nl", "A small country with stroopwafels"],
        )
        self.assertEqual(
            [block.value for block in rows[1]], ["fr", "A large country with baguettes"]
        )

    def test_submission_with_column_deletion_and_insertion(self):
        # Test server-side behaviour in the setting described in
        # https://github.com/wagtail/wagtail/issues/7654

        # This form data represents a submission where there are three columns:
        # country (column id 0), population (column id 3), description (column id 2)
        # Column id 1 is a population column that was deleted before being replaced by the
        # current one with id 3.
        form_data = {
            # table-column-count includes deleted columns, as it's telling the server code
            # the maximum column ID number it should consider
            "table-column-count": "4",
            "table-row-count": "1",
            "table-column-0-type": "country",
            "table-column-0-order": "0",
            "table-column-0-deleted": "",
            "table-column-0-heading": "Country",
            "table-column-1-deleted": "1",
            "table-column-2-type": "text",
            "table-column-2-order": "2",
            "table-column-2-deleted": "",
            "table-column-2-heading": "Description",
            "table-column-3-type": "text",
            "table-column-3-order": "1",
            "table-column-3-deleted": "",
            "table-column-3-heading": "Population",
            "table-row-0-order": "1",
            "table-row-0-deleted": "",
            "table-cell-0-0": "fr",
            "table-cell-0-3": "68000000",
            "table-cell-0-2": "A large country with baguettes",
        }
        table = self.block.value_from_datadict(form_data, {}, "table")

        self.assertIsInstance(table, TypedTable)
        self.assertEqual(len(table.columns), 3)
        self.assertEqual(table.columns[0]["heading"], "Country")
        self.assertEqual(table.columns[1]["heading"], "Population")
        self.assertEqual(table.columns[2]["heading"], "Description")
        rows = list(table.rows)
        self.assertEqual(len(rows), 1)
        self.assertEqual(
            [block.value for block in rows[0]],
            ["fr", "68000000", "A large country with baguettes"],
        )

    def test_to_python(self):
        """
        Test that we can turn JSONish data from the database into a TypedTable instance
        """
        table = self.block.to_python(self.db_data)
        self.assertIsInstance(table, TypedTable)
        self.assertEqual(len(table.columns), 2)
        self.assertEqual(table.columns[0]["heading"], "Country")
        self.assertEqual(table.columns[1]["heading"], "Description")
        rows = list(table.rows)
        self.assertEqual(len(rows), 2)
        self.assertEqual(
            [block.value for block in rows[0]],
            ["nl", "A small country with stroopwafels"],
        )
        self.assertEqual(
            [block.value for block in rows[1]], ["fr", "A large country with baguettes"]
        )

    def test_get_prep_value(self):
        """
        Test that we can turn a TypedTable instance into JSONish data for the database
        """
        table = self.block.value_from_datadict(self.form_data, {}, "table")
        table_data = self.block.get_prep_value(table)
        self.assertEqual(table_data, self.db_data)

    def test_clean(self):
        table = self.block.value_from_datadict(self.form_data, {}, "table")
        # cleaning a valid table should return a TypedTable instance
        cleaned_table = self.block.clean(table)
        self.assertIsInstance(cleaned_table, TypedTable)

        # now retry with invalid data (description is a required field)
        invalid_form_data = self.form_data.copy()
        invalid_form_data["table-cell-0-1"] = ""
        invalid_table = self.block.value_from_datadict(invalid_form_data, {}, "table")

        with self.assertRaises(TypedTableBlockValidationError) as exc_info:
            self.block.clean(invalid_table)

        # table-cell-0-1 is actually cell 1 of row 1 due to the swapped row order in the data
        self.assertTrue(exc_info.exception.cell_errors[1][1])

    def test_render(self):
        table = self.block.value_from_datadict(self.form_data, {}, "table")
        html = self.block.render(table)

        self.assertIn('<th scope="col">Country</th>', html)
        # rendering should use the block renderings of the child blocks ('FR' not 'fr')
        self.assertIn("<td>FR</td>", html)

    def test_validation_error_as_json(self):
        error = TypedTableBlockValidationError(
            cell_errors={
                1: {
                    2: StructBlockValidationError(
                        block_errors={
                            "first_name": ErrorList(
                                [ValidationError("This field is required.")]
                            )
                        }
                    )
                }
            },
            non_block_errors=ErrorList(
                [ValidationError("The maximum number of rows is 1000.")]
            ),
        )
        self.assertEqual(
            get_error_json_data(error),
            {
                "blockErrors": {
                    1: {
                        2: {
                            "blockErrors": {
                                "first_name": {"messages": ["This field is required."]}
                            }
                        }
                    }
                },
                "messages": [
                    "The maximum number of rows is 1000.",
                ],
            },
        )

    def test_validation_error_without_cell_errors(self):
        error = TypedTableBlockValidationError(
            non_block_errors=[ValidationError("The maximum number of rows is 1000.")]
        )
        self.assertEqual(
            get_error_json_data(error),
            {
                "messages": [
                    "The maximum number of rows is 1000.",
                ],
            },
        )

    def test_validation_error_without_non_block_errors(self):
        error = TypedTableBlockValidationError(
            cell_errors={1: {2: ValidationError("This field is required.")}},
        )
        self.assertEqual(
            get_error_json_data(error),
            {
                "blockErrors": {1: {2: {"messages": ["This field is required."]}}},
            },
        )
