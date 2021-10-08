from django.test import TestCase

from wagtail.contrib.typed_table_block.blocks import (
    TypedTable, TypedTableBlock, TypedTableBlockValidationError)
from wagtail.core import blocks


class CountryChoiceBlock(blocks.ChoiceBlock):
    """A ChoiceBlock with a custom rendering, to check that block rendering is honoured"""
    def render_basic(self, value, context=None):
        return value.upper() if value else value


class TestTableBlock(TestCase):
    def setUp(self):
        self.block = TypedTableBlock([
            ('text', blocks.CharBlock()),
            ('country', CountryChoiceBlock(choices=[
                ('be', 'Belgium'),
                ('fr', 'France'),
                ('nl', 'Netherlands'),
            ])),
        ])

        self.form_data = {
            'table-column-count': '2',
            'table-row-count': '3',
            'table-column-0-type': 'country',
            'table-column-0-order': '0',
            'table-column-0-deleted': '',
            'table-column-0-heading': 'Country',
            'table-column-1-type': 'text',
            'table-column-1-order': '1',
            'table-column-1-deleted': '',
            'table-column-1-heading': 'Description',
            'table-row-0-order': '1',
            'table-row-0-deleted': '',
            'table-cell-0-0': 'fr',
            'table-cell-0-1': 'A large country with baguettes',
            'table-row-1-order': '0',
            'table-row-1-deleted': '',
            'table-cell-1-0': 'nl',
            'table-cell-1-1': 'A small country with stroopwafels',
            'table-row-2-order': '2',
            'table-row-2-deleted': '1',
            'table-cell-2-0': 'be',
            'table-cell-2-1': 'A small country with sprouts',
        }

        self.db_data = {
            'columns': [
                {'type': 'country', 'heading': 'Country'},
                {'type': 'text', 'heading': 'Description'},
            ],
            'rows': [
                {'values': ['nl', 'A small country with stroopwafels']},
                {'values': ['fr', 'A large country with baguettes']},
            ],
        }

    def test_value_from_datadict(self):
        """
        Test that we can turn posted form data into a TypedTable instance,
        accounting for row reordering and deleted rows.
        """
        table = self.block.value_from_datadict(self.form_data, {}, 'table')

        self.assertIsInstance(table, TypedTable)
        self.assertEqual(len(table.columns), 2)
        self.assertEqual(table.columns[0]['heading'], 'Country')
        self.assertEqual(table.columns[1]['heading'], 'Description')
        rows = list(table.rows)
        self.assertEqual(len(rows), 2)
        self.assertEqual([block.value for block in rows[0]], ['nl', 'A small country with stroopwafels'])
        self.assertEqual([block.value for block in rows[1]], ['fr', 'A large country with baguettes'])

    def test_to_python(self):
        """
        Test that we can turn JSONish data from the database into a TypedTable instance
        """
        table = self.block.to_python(self.db_data)
        self.assertIsInstance(table, TypedTable)
        self.assertEqual(len(table.columns), 2)
        self.assertEqual(table.columns[0]['heading'], 'Country')
        self.assertEqual(table.columns[1]['heading'], 'Description')
        rows = list(table.rows)
        self.assertEqual(len(rows), 2)
        self.assertEqual([block.value for block in rows[0]], ['nl', 'A small country with stroopwafels'])
        self.assertEqual([block.value for block in rows[1]], ['fr', 'A large country with baguettes'])

    def test_get_prep_value(self):
        """
        Test that we can turn a TypedTable instance into JSONish data for the database
        """
        table = self.block.value_from_datadict(self.form_data, {}, 'table')
        table_data = self.block.get_prep_value(table)
        self.assertEqual(table_data, self.db_data)

    def test_clean(self):
        table = self.block.value_from_datadict(self.form_data, {}, 'table')
        # cleaning a valid table should return a TypedTable instance
        cleaned_table = self.block.clean(table)
        self.assertIsInstance(cleaned_table, TypedTable)

        # now retry with invalid data (description is a required field)
        invalid_form_data = self.form_data.copy()
        invalid_form_data['table-cell-0-1'] = ''
        invalid_table = self.block.value_from_datadict(invalid_form_data, {}, 'table')

        with self.assertRaises(TypedTableBlockValidationError) as exc_info:
            self.block.clean(invalid_table)

        # table-cell-0-1 is actually cell 1 of row 1 due to the swapped row order in the data
        self.assertTrue(exc_info.exception.cell_errors[1][1])

    def test_render(self):
        table = self.block.value_from_datadict(self.form_data, {}, 'table')
        html = self.block.render(table)

        self.assertIn('<th scope="col">Country</th>', html)
        # rendering should use the block renderings of the child blocks ('FR' not 'fr')
        self.assertIn('<td>FR</td>', html)
