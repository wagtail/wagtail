import json

from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import translation
from django.utils.html import escape

from wagtail.contrib.table_block.blocks import DEFAULT_TABLE_OPTIONS, TableBlock
from wagtail.core.models import Page
from wagtail.tests.testapp.models import TableBlockStreamPage
from wagtail.tests.utils import WagtailTestUtils


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

    def test_searchable_content(self):
        value = {'first_row_is_table_header': False, 'first_col_is_header': False,
                 'data': [['Test 1', 'Test 2', 'Test 3'], [None, 'Bar', None],
                          [None, 'Foo', None]]}
        block = TableBlock()
        content = block.get_searchable_content(value)
        self.assertEqual(content, ['Test 1', 'Test 2', 'Test 3', 'Bar', 'Foo', ])

    def test_render_with_extra_context(self):
        """
        Test that extra context variables passed in block.render are passed through
        to the template.
        """
        block = TableBlock(template="tests/blocks/table_block_with_caption.html")

        value = {'first_row_is_table_header': False, 'first_col_is_header': False,
                 'data': [['Test 1', 'Test 2', 'Test 3'], [None, None, None],
                          [None, None, None]]}
        result = block.render(value, context={
            'caption': "A fascinating table."
        })
        self.assertIn("Test 1", result)
        self.assertIn("<div>A fascinating table.</div>", result)


class TestTableBlockForm(WagtailTestUtils, SimpleTestCase):

    def setUp(self):
        # test value for table data
        self.value = {
            'first_row_is_table_header': True,
            'first_col_is_header': True,
            'data': [
                ['Ship', 'Type', 'Status'],
                ['Galactica', 'Battlestar', 'Active'],
                ['Valkyrie', 'Battlestar', 'Destroyed'],
                ['Cylon Basestar', 'Basestar', 'Active'],
                ['Brenik', 'Small Military Vessel', 'Destroyed'],
            ]
        }
        # set language from testing envrionment
        language = translation.get_language()
        if language is not None and len(language) > 2:
            language = language[:2]

        self.default_table_options = DEFAULT_TABLE_OPTIONS.copy()
        self.default_table_options['language'] = language

    def test_default_table_options(self):
        """
        Test options without any custom table_options provided.
        """
        block = TableBlock()
        # check that default_table_options created correctly
        self.assertEqual(block.table_options, block.get_table_options())
        # check that default_table_options used on self
        self.assertEqual(self.default_table_options, block.table_options)
        # check a few individual keys from DEFAULT_TABLE_OPTIONS
        self.assertEqual(DEFAULT_TABLE_OPTIONS['startRows'], block.table_options['startRows'])
        self.assertEqual(DEFAULT_TABLE_OPTIONS['colHeaders'], block.table_options['colHeaders'])
        self.assertEqual(DEFAULT_TABLE_OPTIONS['contextMenu'], block.table_options['contextMenu'])
        self.assertEqual(DEFAULT_TABLE_OPTIONS['editor'], block.table_options['editor'])
        self.assertEqual(DEFAULT_TABLE_OPTIONS['stretchH'], block.table_options['stretchH'])

    def test_table_options_language(self):
        """
        Test that the envrionment's language is used if no language provided.
        """
        # default must always contain a language value
        block = TableBlock()
        self.assertIn('language', block.table_options)
        # French
        translation.activate('fr-fr')
        block_fr = TableBlock()
        self.assertEqual('fr', block_fr.table_options['language'])
        translation.activate('it')
        # Italian
        block_it = TableBlock()
        self.assertEqual('it', block_it.table_options['language'])
        # table_options with language provided, different to envrionment
        block_with_lang = TableBlock(table_options={'language': 'ja'})
        self.assertNotEqual('it', block_with_lang.table_options['language'])
        self.assertEqual('ja', block_with_lang.table_options['language'])
        translation.activate('en')

    def test_table_options_context_menu(self):
        """
        Test how contextMenu is set to default.
        """
        default_context_menu = list(DEFAULT_TABLE_OPTIONS['contextMenu'])  # create copy
        # confirm the default is correct
        table_options = TableBlock().table_options
        self.assertEqual(table_options['contextMenu'], default_context_menu)
        # confirm that when custom option is True, default is still used
        table_options_menu_true = TableBlock(table_options={'contextMenu': True}).table_options
        self.assertEqual(table_options_menu_true['contextMenu'], default_context_menu)
        # confirm menu is removed if False is passed in
        table_options_menu_false = TableBlock(table_options={'contextMenu': False}).table_options
        self.assertEqual(table_options_menu_false['contextMenu'], False)
        # confirm if list passed in, it is used
        table_options_menu_list = TableBlock(table_options={'contextMenu': ['undo', 'redo']}).table_options
        self.assertEqual(table_options_menu_list['contextMenu'], ['undo', 'redo'])
        # test if empty array passed in
        table_options_menu_list = TableBlock(table_options={'contextMenu': []}).table_options
        self.assertEqual(table_options_menu_list['contextMenu'], [])

    def test_table_options_others(self):
        """
        Test simple options overrides get passed correctly.
        """
        block_1_opts = TableBlock(table_options={'startRows': 5, 'startCols': 2}).table_options
        self.assertEqual(block_1_opts['startRows'], 5)
        self.assertEqual(block_1_opts['startCols'], 2)

        block_2_opts = TableBlock(table_options={'stretchH': 'none'}).table_options
        self.assertEqual(block_2_opts['stretchH'], 'none')

        # check value that is not part of the defaults
        block_3_opts = TableBlock(table_options={'allowEmpty': False}).table_options
        self.assertEqual(block_3_opts['allowEmpty'], False)


    def test_tableblock_render_form(self):
        """
        Test the rendered form field generated by TableBlock.
        """
        block = TableBlock()
        html = block.render_form(value=self.value)
        self.assertIn('<script>initTable', html)
        self.assertIn('<div class="field char_field widget-table_input">', html)
        # check that options render in the init function
        self.assertIn('"editor": "text"', html)
        self.assertIn('"autoColumnSize": false', html)
        self.assertIn('"stretchH": "all"', html)

    def test_searchable_content(self):
        """
        Test searchable content is created correctly.
        """
        block = TableBlock()
        search_content = block.get_searchable_content(value=self.value)
        self.assertIn('Galactica', search_content)
        self.assertIn('Brenik', search_content)


class TestTableBlockPageEdit(TestCase, WagtailTestUtils):
    def setUp(self):
        self.value = {
            'first_row_is_table_header': True,
            'first_col_is_header': True,
            'data': [
                ['Ship', 'Type', 'Status'],
                ['Galactica', 'Battlestar', 'Active'],
                ['Valkyrie', 'Battlestar', 'Destroyed'],
                ['Cylon Basestar', 'Basestar', 'Active'],
                ['Brenik', 'Small Military Vessel', 'Destroyed'],
            ]
        }
        self.root_page = Page.objects.get(id=2)
        table_block_page_instance = TableBlockStreamPage(
            title='Ships',
            table=json.dumps([{'type': 'table', 'value': self.value}])
        )
        self.table_block_page = self.root_page.add_child(instance=table_block_page_instance)
        self.user = self.login()

    def test_page_edit_page_view(self):
        """
        Test that edit page loads with saved table data and correct init function.
        """
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.table_block_page.id,)))
        # check page + field renders
        self.assertContains(response, '<div class="field char_field widget-table_input fieldname-table">')
        # check data
        self.assertContains(response, 'Battlestar')
        self.assertContains(response, 'Galactica')
        # check init
        self.assertContains(response, 'initTable("table\\u002D0\\u002Dvalue"')
        self.assertContains(response, 'minSpareRows')
        self.assertContains(response, 'startRows')
