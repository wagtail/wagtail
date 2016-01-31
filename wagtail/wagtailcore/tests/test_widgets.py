from django.test import TestCase
from wagtail.wagtailcore.fields import BaseTextAreaWidget, RichTextArea


class TestBaseTextAreaWidget(TestCase):

    def test_get_panel_implemented(self):
        with self.assertRaises(NotImplementedError):
            widget = BaseTextAreaWidget()
            widget.get_panel()

    def test_render_js_init(self):
        widget = BaseTextAreaWidget()
        js_init = widget.render_js_init('test-id', 'test', None)
        self.assertIsInstance(js_init, unicode)
        self.assertEqual(len(js_init), 0)


class TestRichTextAreaWidget(TestCase):

    def test_get_panel_implemented(self):
        from wagtail.wagtailadmin.edit_handlers import RichTextFieldPanel
        widget = RichTextArea()
        panel_proxy = widget.get_panel()
        panel = panel_proxy(None)
        self.assertIsInstance(panel, RichTextFieldPanel)

    def test_widget_default_render_js_init(self):
        widget = RichTextArea()
        js_init = widget.render_js_init('test-id', 'test', None)
        self.assertIsInstance(js_init, unicode)
        self.assertEqual(js_init, "makeRichTextEditable(\"test-id\", null);")

    def test_widget_eit_config_render_js_init(self):
        custom_widget = RichTextArea(editor_config={'plugins': {'halloheadings': {'formatBlocks': ['p', 'h2']}}})
        js_init = custom_widget.render_js_init('test-id', 'test', None)
        self.assertIsInstance(js_init, unicode)
        self.assertEqual(js_init, "makeRichTextEditable(\"test-id\", {"
                                  "\"plugins\": {\"halloheadings\": {\"formatBlocks\": [\"p\", \"h2\"]}}});"
                         )



