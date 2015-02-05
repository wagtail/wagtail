import unittest

from django import forms
from django.core.exceptions import ValidationError

from wagtail.wagtailadmin import blocks


class TestFieldBlock(unittest.TestCase):
    def test_charfield_render(self):
        block = blocks.FieldBlock(forms.CharField())
        html = block.render("Hello world!")

        self.assertEqual(html, "Hello world!")

    def test_charfield_render_form(self):
        block = blocks.FieldBlock(forms.CharField())
        html = block.render_form("Hello world!")

        self.assertIn('<div class="field char_field">', html)
        self.assertIn('<input id="" name="" type="text" value="Hello world!" />', html)

    def test_charfield_render_form_with_prefix(self):
        block = blocks.FieldBlock(forms.CharField())
        html = block.render_form("Hello world!", prefix='foo')

        self.assertIn('<input id="foo" name="foo" type="text" value="Hello world!" />', html)

    def test_charfield_render_form_with_error(self):
        block = blocks.FieldBlock(forms.CharField())
        html = block.render_form("Hello world!", error=ValidationError("This field is required."))

        self.assertIn('This field is required.', html)

    @unittest.expectedFailure
    def test_choicefield_render(self):
        block = blocks.FieldBlock(forms.ChoiceField(choices=(
            ('choice-1', "Choice 1"),
            ('choice-2', "Choice 2"),
        )))
        html = block.render('choice-2')

        self.assertEqual(html, "Choice 2")

    def test_choicefield_render_form(self):
        block = blocks.FieldBlock(forms.ChoiceField(choices=(
            ('choice-1', "Choice 1"),
            ('choice-2', "Choice 2"),
        )))
        html = block.render_form('choice-2')

        self.assertIn('<div class="field choice_field">', html)
        self.assertIn('<select id="" name="">', html)
        self.assertIn('<option value="choice-1">Choice 1</option>', html)
        self.assertIn('<option value="choice-2" selected="selected">Choice 2</option>', html)
