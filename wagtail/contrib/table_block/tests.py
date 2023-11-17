import json
import unittest

from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import translation

from wagtail.blocks.field_block import FieldBlockAdapter
from wagtail.contrib.table_block.blocks import DEFAULT_TABLE_OPTIONS, TableBlock
from wagtail.models import Page
from wagtail.test.testapp.models import TableBlockStreamPage
from wagtail.test.utils import WagtailTestUtils

from .blocks import TableInput


class TestTableBlock(TestCase):
    def setUp(self):
        self.default_table_options = {
            "minSpareRows": 0,
            "startRows": 3,
            "startCols": 3,
            "colHeaders": False,
            "rowHeaders": False,
            "contextMenu": True,
            "editor": "text",
            "stretchH": "all",
            "height": 108,
            "language": "en",
            "renderer": "text",
            "autoColumnSize": False,
        }

    def test_table_block_render(self):
        """
        Test a generic render.
        """
        value = {
            "first_row_is_table_header": False,
            "first_col_is_header": False,
            "data": [
                ["Test 1", "Test 2", "Test 3"],
                [None, None, None],
                [None, None, None],
            ],
        }
        block = TableBlock()
        result = block.render(value)
        expected = """
            <table>
                <tbody>
                    <tr><td>Test 1</td><td>Test 2</td><td>Test 3</td></tr>
                    <tr><td></td><td></td><td></td></tr>
                    <tr><td></td><td></td><td></td></tr>
                </tbody>
            </table>
        """

        self.assertHTMLEqual(result, expected)
        self.assertIn("Test 2", result)

    def test_table_block_alignment_render(self):
        """
        Test a generic render with some cells aligned.
        """
        value = {
            "first_row_is_table_header": True,
            "first_col_is_header": False,
            "cell": [
                {"row": 0, "col": 1, "className": "htLeft"},
                {"row": 1, "col": 1, "className": "htRight"},
            ],
            "data": [
                ["Test 1", "Test 2", "Test 3"],
                [None, None, None],
                [None, None, None],
            ],
        }
        block = TableBlock()
        result = block.render(value)
        expected = """
            <table>
                <thead>
                    <tr><th scope="col">Test 1</th><th scope="col" class="htLeft">Test 2</th><th scope="col">Test 3</th></tr>
                </thead>
                <tbody>
                    <tr><td></td><td class="htRight"></td><td></td></tr>
                    <tr><td></td><td></td><td></td></tr>
                </tbody>
            </table>
        """

        self.assertHTMLEqual(result, expected)
        self.assertIn("Test 2", result)

    def test_render_empty_table(self):
        """
        An empty table should render okay.
        """
        block = TableBlock()
        result = block.render(
            {
                "first_row_is_table_header": False,
                "first_col_is_header": False,
                "data": [[None, None, None], [None, None, None], [None, None, None]],
            }
        )
        expected = """
            <table>
                <tbody>
                    <tr><td></td><td></td><td></td></tr>
                    <tr><td></td><td></td><td></td></tr>
                    <tr><td></td><td></td><td></td></tr>
                </tbody>
            </table>
        """
        self.assertHTMLEqual(result, expected)

    def test_do_not_render_html(self):
        """
        Ensure that raw html doesn't render
        by default.
        """
        value = {
            "first_row_is_table_header": False,
            "first_col_is_header": False,
            "data": [
                ["<p><strong>Test</strong></p>", None, None],
                [None, None, None],
                [None, None, None],
            ],
        }

        expected = """
            <table>
                <tbody>
                    <tr><td>&lt;p&gt;&lt;strong&gt;Test&lt;/strong&gt;&lt;/p&gt;</td><td></td><td></td></tr>
                    <tr><td></td><td></td><td></td></tr>
                    <tr><td></td><td></td><td></td></tr>
                </tbody>
            </table>
        """

        block = TableBlock()
        result = block.render(value)
        self.assertHTMLEqual(result, expected)

    def test_row_headers(self):
        """
        Ensure that row headers are properly rendered.
        """
        value = {
            "first_row_is_table_header": True,
            "first_col_is_header": False,
            "data": [["Foo", "Bar", "Baz"], [None, None, None], [None, None, None]],
        }

        expected = """
            <table>
                <thead>
                    <tr><th scope="col">Foo</th><th scope="col">Bar</th><th scope="col">Baz</th></tr>
                </thead>
                <tbody>
                    <tr><td></td><td></td><td></td></tr>
                    <tr><td></td><td></td><td></td></tr>
                </tbody>
            </table>
        """
        block = TableBlock()
        result = block.render(value)
        self.assertHTMLEqual(result, expected)

    def test_column_headers(self):
        """
        Ensure that column headers are properly rendered.
        """
        value = {
            "first_row_is_table_header": False,
            "first_col_is_header": True,
            "data": [
                ["Foo", "Bar", "Baz"],
                ["one", "two", "three"],
                ["four", "five", "six"],
            ],
        }

        expected = """
            <table>
                <tbody>
                    <tr><th scope="row">Foo</th><td>Bar</td><td>Baz</td></tr>
                    <tr><th scope="row">one</th><td>two</td><td>three</td></tr>
                    <tr><th scope="row">four</th><td>five</td><td>six</td></tr>
                </tbody>
            </table>
        """
        block = TableBlock()
        result = block.render(value)
        self.assertHTMLEqual(result, expected)

    def test_row_and_column_headers(self):
        """
        Test row and column headers at the same time.
        """
        value = {
            "first_row_is_table_header": True,
            "first_col_is_header": True,
            "data": [
                ["Foo", "Bar", "Baz"],
                ["one", "two", "three"],
                ["four", "five", "six"],
            ],
        }

        expected = """
            <table>
                <thead>
                    <tr><th scope="col">Foo</th><th scope="col">Bar</th><th scope="col">Baz</th></tr>
                </thead>
                <tbody>
                    <tr><th scope="row">one</th><td>two</td><td>three</td></tr>
                    <tr><th scope="row">four</th><td>five</td><td>six</td></tr>
                </tbody>
            </table>
        """
        block = TableBlock()
        result = block.render(value)
        self.assertHTMLEqual(result, expected)

    def test_value_for_and_from_form(self):
        """
        Make sure we get back good json and make
        sure it translates back to python.
        """
        value = {
            "first_row_is_table_header": False,
            "first_col_is_header": False,
            "data": [["Foo", 1, None], [3.5, "Bar", "Baz"]],
        }
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
        self.assertIs(block1.is_html_renderer(), False)

        # TableBlock with altered table_options
        new_options = self.default_table_options.copy()
        new_options["renderer"] = "html"
        block2 = TableBlock(table_options=new_options)
        self.assertIs(block2.is_html_renderer(), True)

    def test_searchable_content(self):
        value = {
            "first_row_is_table_header": False,
            "first_col_is_header": False,
            "data": [
                ["Test 1", "Test 2", "Test 3"],
                [None, "Bar", None],
                [None, "Foo", None],
            ],
        }
        block = TableBlock()
        content = block.get_searchable_content(value)
        self.assertEqual(
            content,
            [
                "Test 1",
                "Test 2",
                "Test 3",
                "Bar",
                "Foo",
            ],
        )

    def test_searchable_content_for_null_block(self):
        value = None
        block = TableBlock()
        content = block.get_searchable_content(value)
        self.assertEqual(content, [])

    def test_render_with_extra_context(self):
        """
        Test that extra context variables passed in block.render are passed through
        to the template.
        """
        block = TableBlock(template="tests/blocks/table_block_with_caption.html")

        value = {
            "first_row_is_table_header": False,
            "first_col_is_header": False,
            "data": [
                ["Test 1", "Test 2", "Test 3"],
                [None, None, None],
                [None, None, None],
            ],
        }
        result = block.render(value, context={"caption": "A fascinating table."})
        self.assertIn("Test 1", result)
        self.assertIn("<div>A fascinating table.</div>", result)

    def test_table_block_caption_render(self):
        """
        Test a generic render with caption.
        """
        value = {
            "table_caption": "caption",
            "first_row_is_table_header": False,
            "first_col_is_header": False,
            "data": [
                ["Test 1", "Test 2", "Test 3"],
                [None, None, None],
                [None, None, None],
            ],
        }
        block = TableBlock()
        result = block.render(value)
        expected = """
            <table>
                <caption>caption</caption>
                <tbody>
                    <tr><td>Test 1</td><td>Test 2</td><td>Test 3</td></tr>
                    <tr><td></td><td></td><td></td></tr>
                    <tr><td></td><td></td><td></td></tr>
                </tbody>
            </table>
        """
        self.assertHTMLEqual(result, expected)
        self.assertIn("Test 2", result)

    def test_empty_table_block_is_not_rendered(self):
        """
        Test an empty table is not rendered.
        """
        value = None
        block = TableBlock()
        result = block.render(value)
        expected = ""

        self.assertHTMLEqual(result, expected)
        self.assertNotIn("None", result)

    def test_merge_cells_render(self):
        """
        Test that merged table cells are rendered.
        """
        value = {
            "first_row_is_table_header": False,
            "first_col_is_header": False,
            "data": [
                ["one", None, "two"],
                ["three", "four", "five"],
                ["six", "seven", None],
            ],
            "cell": [
                {"row": 0, "col": 1, "hidden": True},
                {"row": 2, "col": 2, "hidden": True},
            ],
            "mergeCells": [
                {"row": 0, "col": 0, "rowspan": 1, "colspan": 2},
                {"row": 1, "col": 2, "rowspan": 2, "colspan": 1},
            ],
        }
        block = TableBlock()
        result = block.render(value)
        expected = """
            <table>
                <tbody>
                    <tr><td rowspan="1" colspan="2">one</td><td>two</td></tr>
                    <tr><td>three</td><td>four</td><td rowspan="2" colspan="1">five</td></tr>
                    <tr><td>six</td><td>seven</td></tr>
                </tbody>
            </table>
        """
        self.assertHTMLEqual(result, expected)


class TestTableBlockForm(WagtailTestUtils, SimpleTestCase):
    def setUp(self):
        # test value for table data
        self.value = {
            "first_row_is_table_header": True,
            "first_col_is_header": True,
            "data": [
                ["Ship", "Type", "Status"],
                ["Galactica", "Battlestar", "Active"],
                ["Valkyrie", "Battlestar", "Destroyed"],
                ["Cylon Basestar", "Basestar", "Active"],
                ["Brenik", "Small Military Vessel", "Destroyed"],
            ],
        }
        # set language from testing environment
        language = translation.get_language()

        self.default_table_options = DEFAULT_TABLE_OPTIONS.copy()
        self.default_table_options["language"] = language

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
        self.assertEqual(
            DEFAULT_TABLE_OPTIONS["startRows"], block.table_options["startRows"]
        )
        self.assertEqual(
            DEFAULT_TABLE_OPTIONS["colHeaders"], block.table_options["colHeaders"]
        )
        self.assertEqual(
            DEFAULT_TABLE_OPTIONS["contextMenu"], block.table_options["contextMenu"]
        )
        self.assertEqual(DEFAULT_TABLE_OPTIONS["editor"], block.table_options["editor"])
        self.assertEqual(
            DEFAULT_TABLE_OPTIONS["stretchH"], block.table_options["stretchH"]
        )

    def test_table_options_language(self):
        """
        Test that the environment's language is used if no language provided.
        """
        # default must always contain a language value
        block = TableBlock()
        self.assertIn("language", block.table_options)
        # French
        translation.activate("fr-fr")
        block_fr = TableBlock()
        self.assertEqual("fr-fr", block_fr.table_options["language"])
        translation.activate("it")
        # Italian
        block_it = TableBlock()
        self.assertEqual("it", block_it.table_options["language"])
        # table_options with language provided, different to environment
        block_with_lang = TableBlock(table_options={"language": "ja"})
        self.assertNotEqual("it", block_with_lang.table_options["language"])
        self.assertEqual("ja", block_with_lang.table_options["language"])
        translation.activate("en")

    def test_table_options_context_menu(self):
        """
        Test how contextMenu is set to default.
        """
        default_context_menu = list(DEFAULT_TABLE_OPTIONS["contextMenu"])  # create copy
        # confirm the default is correct
        table_options = TableBlock().table_options
        self.assertEqual(table_options["contextMenu"], default_context_menu)
        # confirm that when custom option is True, default is still used
        table_options_menu_true = TableBlock(
            table_options={"contextMenu": True}
        ).table_options
        self.assertEqual(table_options_menu_true["contextMenu"], default_context_menu)
        # confirm menu is removed if False is passed in
        table_options_menu_false = TableBlock(
            table_options={"contextMenu": False}
        ).table_options
        self.assertIs(table_options_menu_false["contextMenu"], False)
        # confirm if list passed in, it is used
        table_options_menu_list = TableBlock(
            table_options={"contextMenu": ["undo", "redo"]}
        ).table_options
        self.assertEqual(table_options_menu_list["contextMenu"], ["undo", "redo"])
        # test if empty array passed in
        table_options_menu_list = TableBlock(
            table_options={"contextMenu": []}
        ).table_options
        self.assertEqual(table_options_menu_list["contextMenu"], [])

    def test_table_options_others(self):
        """
        Test simple options overrides get passed correctly.
        """
        block_1_opts = TableBlock(
            table_options={"startRows": 5, "startCols": 2}
        ).table_options
        self.assertEqual(block_1_opts["startRows"], 5)
        self.assertEqual(block_1_opts["startCols"], 2)

        block_2_opts = TableBlock(table_options={"stretchH": "none"}).table_options
        self.assertEqual(block_2_opts["stretchH"], "none")

        # check value that is not part of the defaults
        block_3_opts = TableBlock(table_options={"allowEmpty": False}).table_options
        self.assertIs(block_3_opts["allowEmpty"], False)

    def test_adapt(self):
        block = TableBlock()

        block.set_name("test_tableblock")
        js_args = FieldBlockAdapter().js_args(block)

        self.assertEqual(js_args[0], "test_tableblock")
        self.assertIsInstance(js_args[1], TableInput)
        self.assertEqual(
            js_args[2],
            {
                "label": "Test tableblock",
                "required": True,
                "icon": "table",
                "classname": "w-field w-field--char_field w-field--table_input",
                "showAddCommentButton": True,
                "strings": {"ADD_COMMENT": "Add Comment"},
            },
        )

    def test_searchable_content(self):
        """
        Test searchable content is created correctly.
        """
        block = TableBlock()
        search_content = block.get_searchable_content(value=self.value)
        self.assertIn("Galactica", search_content)
        self.assertIn("Brenik", search_content)


# TODO(telepath) replace this with a functional test
class TestTableBlockPageEdit(WagtailTestUtils, TestCase):
    def setUp(self):
        self.value = {
            "first_row_is_table_header": True,
            "first_col_is_header": True,
            "data": [
                ["Ship", "Type", "Status"],
                ["Galactica", "Battlestar", "Active"],
                ["Valkyrie", "Battlestar", "Destroyed"],
                ["Cylon Basestar", "Basestar", "Active"],
                ["Brenik", "Small Military Vessel", "Destroyed"],
            ],
        }
        self.root_page = Page.objects.get(id=2)
        table_block_page_instance = TableBlockStreamPage(
            title="Ships", table=json.dumps([{"type": "table", "value": self.value}])
        )
        self.table_block_page = self.root_page.add_child(
            instance=table_block_page_instance
        )
        self.user = self.login()

    @unittest.expectedFailure
    def test_page_edit_page_view(self):
        """
        Test that edit page loads with saved table data and correct init function.
        """
        response = self.client.get(
            reverse("wagtailadmin_pages:edit", args=(self.table_block_page.id,))
        )
        # check page + field renders
        self.assertContains(
            response,
            '<div data-contentpath="table" class="w-field w-field--char_field w-field--table_input">',
        )
        # check data
        self.assertContains(response, "Battlestar")
        self.assertContains(response, "Galactica")
        # check init
        self.assertContains(response, 'initTable("table\\u002D0\\u002Dvalue"')
        self.assertContains(response, "minSpareRows")
        self.assertContains(response, "startRows")
