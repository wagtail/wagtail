from django.test import TestCase
from wagtail.wagtailcore.fields import RichTextField, RichTextArea


class TestRichTextField(TestCase):

    def test_formfield_widget_default(self):
        field = RichTextField()
        formfield = field.formfield()
        self.assertIsInstance(formfield.widget, RichTextArea)

    def test_formfield_widget_custom(self):
        custom_widget = RichTextArea(editor_config={'custom': {'testix': {'formatBlocks': ['p', 'h2']}}})
        field = RichTextField(widget=custom_widget)
        formfield = field.formfield()

        self.assertEqual(formfield.widget, custom_widget)
