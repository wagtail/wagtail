from django.test import TestCase
from wagtail.wagtailcore.fields import RichTextField


class TestRichTextField(TestCase):

    def test_has_field_options_attribute(self):
        field = RichTextField()
        self.assertTrue(hasattr(field, 'field_options'))

    def test_field_options_widget_default(self):
        field = RichTextField()
        self.assertIsNone(field.field_options.get('widget'))

    def test_formfield_has_widget(self):
        field = RichTextField()
        formfield = field.formfield()
        self.assertTrue(hasattr(formfield, 'widget'))

    def test_formfield_widget_default(self):
        from wagtail.wagtailcore.fields import RichTextArea
        field = RichTextField()
        formfield = field.formfield()
        self.assertIsInstance(formfield.widget, RichTextArea)
        self.assertTrue(hasattr(field.formfield().widget, 'editor_config'))

    def test_formfield_widget_custom(self):
        from wagtail.wagtailcore.fields import BaseTextAreaWidget

        class CustomTextArea(BaseTextAreaWidget):
            def get_panel(self):
                pass

        custom_widget = CustomTextArea(editor_config={'custom': {'testix': {'formatBlocks': ['p', 'h2']}}})
        field = RichTextField(widget=custom_widget)
        formfield = field.formfield()
        self.assertIsInstance(formfield.widget, CustomTextArea)
        self.assertTrue(hasattr(field.formfield().widget, 'editor_config'))