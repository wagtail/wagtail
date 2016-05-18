from __future__ import absolute_import, unicode_literals

from django.test import TestCase
from django.utils.html import escape

from wagtail.contrib.table_block.fields import TableBlock


def tiny_escape(val):
    """
    Helper function used in building a test html
    table.
    """
    return '' if val is None else escape(val)


def get_test_html_from_value(value):
    """
    Generate a test html from a TableBlock value.
    Individual column values are escaped because
    that's what we expect from the TableBlock.
    """
    data = list(value['data'])  # Make a copy
    table = '<table>'
    if value['first_row_is_table_header']:
        row_header = data.pop(0)
        table += '<thead><tr>'
        for th in row_header:
            table += '<th>%s</th>' % tiny_escape(th)
        table += '</tr></thead>'
    table += '<tbody>'
    for row in data:
        table += '<tr>'
        first = True
        for col in row:
            if value['first_col_is_header'] and first:
                table += '<th>%s</th>' % tiny_escape(col)
            else:
                table += '<td>%s</td>' % tiny_escape(col)
            first = False
        table += '</tr>'
    table += '</tbody></table>'
    return table


class TestTableBlockRenderingBase(TestCase):

    def setUp(self):
        self.default_table_options = {
            'minSpareRows': 0,
            'startRows': 3,
            'startCols': 3,
            'colHeaders': False,
            'rowHeaders': False,
            'contextMenu': True,
            'editor': 'text',
            'stretchH': 'all',
            'height': 108,
            'language': 'en',
            'renderer': 'text',
            'autoColumnSize': False,
        }

        self.default_value = {'first_row_is_table_header': False,
                              'first_col_is_header': False, 'data': [[None, None, None],
                                                                     [None, None, None], [None, None, None]]}

        self.default_expected = get_test_html_from_value(self.default_value)


class TestTableBlock(TestTableBlockRenderingBase):

    def test_table_block_render(self):
        """
        Test a generic render.
        """
        value = {'first_row_is_table_header': False, 'first_col_is_header': False,
                 'data': [['Test 1', 'Test 2', 'Test 3'], [None, None, None],
                          [None, None, None]]}
        block = TableBlock()
        result = block.render(value)
        expected = get_test_html_from_value(value)

        self.assertHTMLEqual(result, expected)
        self.assertIn('Test 2', result)


    def test_render_empty_table(self):
        """
        An empty table should render okay.
        """
        block = TableBlock()
        result = block.render(self.default_value)
        self.assertHTMLEqual(result, self.default_expected)


    def test_do_not_render_html(self):
        """
        Ensure that raw html doesn't render
        by default.
        """
        value = {'first_row_is_table_header': False, 'first_col_is_header': False,
                 'data': [['<p><strong>Test</strong></p>', None, None], [None, None, None],
                          [None, None, None]]}

        expected = get_test_html_from_value(value)

        block = TableBlock()
        result = block.render(value)
        self.assertHTMLEqual(result, expected)


    def test_row_headers(self):
        """
        Ensure that row headers are properly rendered.
        """
        value = {'first_row_is_table_header': True, 'first_col_is_header': False,
                 'data': [['Foo', 'Bar', 'Baz'], [None, None, None], [None, None, None]]}

        expected = get_test_html_from_value(value)
        block = TableBlock()
        result = block.render(value)
        self.assertHTMLEqual(result, expected)

    def test_column_headers(self):
        """
        Ensure that column headers are properly rendered.
        """
        value = {'first_row_is_table_header': False, 'first_col_is_header': True,
                 'data': [['Foo', 'Bar', 'Baz'], ['one', 'two', 'three'], ['four', 'five', 'six']]}

        expected = get_test_html_from_value(value)
        block = TableBlock()
        result = block.render(value)
        self.assertHTMLEqual(result, expected)


    def test_row_and_column_headers(self):
        """
        Test row and column headers at the same time.
        """
        value = {'first_row_is_table_header': True, 'first_col_is_header': True,
                 'data': [['Foo', 'Bar', 'Baz'], ['one', 'two', 'three'], ['four', 'five', 'six']]}

        expected = get_test_html_from_value(value)
        block = TableBlock()
        result = block.render(value)
        self.assertHTMLEqual(result, expected)


    def test_value_for_and_from_form(self):
        """
        Make sure we get back good json and make
        sure it translates back to python.
        """
        value = {'first_row_is_table_header': False, 'first_col_is_header': False,
                 'data': [['Foo', 1, None], [3.5, 'Bar', 'Baz']]}
        block = TableBlock()
        expected_json = '{"first_row_is_table_header": false, "first_col_is_header": false, "data": [["Foo", 1, null], [3.5, "Bar", "Baz"]]}'
        returned_json = block.value_for_form(value)

        self.assertJSONEqual(expected_json, returned_json)
        self.assertEqual(block.value_from_form(returned_json), value)


    def test_is_html_renderer(self):
        """
        Test that settings flow through correctly to
        the is_html_renderer method.
        """
        # TableBlock with default table_options
        block1 = TableBlock()
        self.assertEqual(block1.is_html_renderer(), False)

        # TableBlock with altered table_options
        new_options = self.default_table_options.copy()
        new_options['renderer'] = 'html'
        block2 = TableBlock(table_options=new_options)
        self.assertEqual(block2.is_html_renderer(), True)
