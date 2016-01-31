from django.test import TestCase
from wagtail.wagtailadmin.edit_handlers import RichTextFieldPanel

from wagtail.wagtailcore.fields import BaseTextAreaWidget, RichTextArea


class TestBaseTextAreaWidget(TestCase):

    def test_get_panel_implemented(self):
        widget = BaseTextAreaWidget()

        with self.assertRaises(NotImplementedError):
            widget.get_panel()


class TestRichTextAreaWidget(TestCase):

    def test_get_panel(self):
        widget = RichTextArea()
        panel_class = widget.get_panel()

        self.assertEqual(panel_class, RichTextFieldPanel)

    def test_widget_default_render_js_init(self):
        widget = RichTextArea()
        js_init = widget.render_js_init('test-id', 'test', None)

        self.assertEqual(js_init, 'makeRichTextEditable("test-id", null);')

    def test_widget_eit_config_render_js_init(self):
        custom_widget = RichTextArea(editor_config={'plugins': {'halloheadings': {'formatBlocks': ['p', 'h2']}}})
        js_init = custom_widget.render_js_init('test-id', 'test', None)

        self.assertEqual(js_init, 'makeRichTextEditable("test-id", {'
                                  '"plugins": {"halloheadings": {"formatBlocks": ["p", "h2"]}}});'
                         )
