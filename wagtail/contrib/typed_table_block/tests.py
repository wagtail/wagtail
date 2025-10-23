from django.core.exceptions import ValidationError
from django.forms.utils import ErrorList
from django.test import TestCase

from wagtail import blocks
from wagtail.blocks.base import get_error_json_data
from wagtail.blocks.definition_lookup import BlockDefinitionLookup
from wagtail.blocks.struct_block import StructBlockValidationError
from wagtail.contrib.typed_table_block.blocks import (
    TypedTable,
    TypedTableBlock,
    TypedTableBlockAdapter,
    TypedTableBlockValidationError,
)


class CountryChoiceBlock(blocks.ChoiceBlock):
    """A ChoiceBlock with a custom rendering and API representation, to check that block rendering is honoured"""

    def render_basic(self, value, context=None):
        return value.upper() if value else value

    def get_api_representation(self, value, context=None):
        return f".{value}" if value else value


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
            "table-caption": "Countries and their food",
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
            "caption": "Countries and their food",
        }

        self.api_data = {
            "columns": [
                {"type": "country", "heading": "Country"},
                {"type": "text", "heading": "Description"},
            ],
            "rows": [
                {"values": [".nl", "A small country with stroopwafels"]},
                {"values": [".fr", "A large country with baguettes"]},
            ],
            "caption": "Countries and their food",
        }

    def test_value_from_datadict(self):
        """
        Test that we can turn posted form data into a TypedTable instance,
        accounting for row reordering and deleted rows.
        """
        table = self.block.value_from_datadict(self.form_data, {}, "table")

        self.assertIsInstance(table, TypedTable)
        self.assertEqual(table.caption, "Countries and their food")
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
            "table-caption": "Countries and their food",
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
        self.assertEqual(table.caption, "Countries and their food")
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

    def test_normalize(self):
        # Should be able to handle JSONish data from the database, which can be
        # useful when defining a default value for a TypedTableBlock
        table = self.block.normalize(self.db_data)
        self.assertEqual(table.caption, "Countries and their food")
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

        # For a TypedTable instance, normalize should return the instance as-is
        normalized_table = self.block.normalize(table)
        self.assertIs(normalized_table, table)

        # Should normalize None to an empty TypedTable
        none_value = self.block.normalize(None)
        self.assertIsInstance(none_value, TypedTable)
        self.assertEqual(none_value.columns, [])
        self.assertEqual(none_value.row_data, [])
        self.assertEqual(none_value.caption, "")

    def test_to_python(self):
        """
        Test that we can turn JSONish data from the database into a TypedTable instance
        """
        table = self.block.to_python(self.db_data)
        self.assertEqual(table.caption, "Countries and their food")
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

    def test_get_api_representation(self):
        """
        Test that the API representation honours custom representations of child blocks
        """
        table = self.block.to_python(self.db_data)
        table_api_representation = self.block.get_api_representation(table)
        self.assertEqual(table_api_representation, self.api_data)

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

        self.assertIn("<caption>Countries and their food</caption>", html)
        self.assertIn('<th scope="col">Country</th>', html)
        # rendering should use the block renderings of the child blocks ('FR' not 'fr')
        self.assertIn("<td>FR</td>", html)

    def test_adapt(self):
        block = TypedTableBlock(description="A table of countries and their food")

        block.set_name("test_typedtableblock")
        js_args = TypedTableBlockAdapter().js_args(block)

        self.assertEqual(js_args[0], "test_typedtableblock")
        self.assertEqual(
            js_args[-1],
            {
                "label": "Test typedtableblock",
                "description": "A table of countries and their food",
                "required": False,
                "icon": "table",
                "blockDefId": block.definition_prefix,
                "isPreviewable": block.is_previewable,
                "attrs": {},
                "strings": {
                    "CAPTION": "Caption",
                    "CAPTION_HELP_TEXT": (
                        "A heading that identifies the overall topic of the table, and is useful for screen reader users."
                    ),
                    "ADD_COLUMN": "Add column",
                    "ADD_ROW": "Add row",
                    "COLUMN_HEADING": "Column heading",
                    "INSERT_COLUMN": "Insert column",
                    "DELETE_COLUMN": "Delete column",
                    "INSERT_ROW": "Insert row",
                    "DELETE_ROW": "Delete row",
                },
            },
        )

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

    def test_get_searchable_content_includes_caption_headings_and_cells(self):
        columns = [
            {"heading": "Fruit", "type": "text"},
            {"heading": "Quantity", "type": "text"},
        ]

        row_data = [{"values": ["Apple", "5"]}, {"values": ["Banana", "10"]}]

        value = self.block.to_python(
            {"columns": columns, "rows": row_data, "caption": "This is a fruit table"}
        )

        content = self.block.get_searchable_content(value)

        expected_content = [
            "This is a fruit table",
            "Fruit",
            "Quantity",
            "Apple",
            "5",
            "Banana",
            "10",
        ]

        self.assertEqual(content, expected_content)


class TestBlockDefinitionLookup(TestCase):
    def test_block_lookup(self):
        lookup = BlockDefinitionLookup(
            {
                0: ("wagtail.blocks.CharBlock", [], {"required": True}),
                1: (
                    "wagtail.blocks.ChoiceBlock",
                    [],
                    {
                        "choices": [
                            ("be", "Belgium"),
                            ("fr", "France"),
                            ("nl", "Netherlands"),
                        ]
                    },
                ),
                2: (
                    "wagtail.contrib.typed_table_block.blocks.TypedTableBlock",
                    [
                        [
                            ("text", 0),
                            ("country", 1),
                        ],
                    ],
                    {},
                ),
            }
        )
        struct_block = lookup.get_block(2)
        self.assertIsInstance(struct_block, TypedTableBlock)
        text_block = struct_block.child_blocks["text"]
        self.assertIsInstance(text_block, blocks.CharBlock)
        self.assertTrue(text_block.required)
        country_block = struct_block.child_blocks["country"]
        self.assertIsInstance(country_block, blocks.ChoiceBlock)
