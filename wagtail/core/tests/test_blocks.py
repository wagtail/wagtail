# -*- coding: utf-8 -*
import base64
import collections
import json
import unittest
from datetime import date, datetime
from decimal import Decimal

# non-standard import name for ugettext_lazy, to prevent strings from being picked up for translation
from django import forms
from django.core.exceptions import ValidationError
from django.forms.utils import ErrorList
from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase
from django.utils.html import format_html
from django.utils.safestring import SafeData, mark_safe
from django.utils.translation import ugettext_lazy as __

from wagtail.core import blocks
from wagtail.core.models import Page
from wagtail.core.rich_text import RichText
from wagtail.tests.testapp.blocks import LinkBlock as CustomLinkBlock
from wagtail.tests.testapp.blocks import SectionBlock
from wagtail.tests.testapp.models import EventPage, SimplePage
from wagtail.tests.utils import WagtailTestUtils


class FooStreamBlock(blocks.StreamBlock):
    text = blocks.CharBlock()
    error = 'At least one block must say "foo"'

    def clean(self, value):
        value = super().clean(value)
        if not any(block.value == 'foo' for block in value):
            raise blocks.StreamBlockValidationError(non_block_errors=ErrorList([self.error]))
        return value


class ContextCharBlock(blocks.CharBlock):
    def get_context(self, value, parent_context=None):
        value = str(value).upper()
        return super(blocks.CharBlock, self).get_context(value, parent_context)


class TestFieldBlock(WagtailTestUtils, SimpleTestCase):
    def test_charfield_render(self):
        block = blocks.CharBlock()
        html = block.render("Hello world!")

        self.assertEqual(html, "Hello world!")

    def test_charfield_render_with_template(self):
        block = blocks.CharBlock(template='tests/blocks/heading_block.html')
        html = block.render("Hello world!")

        self.assertEqual(html, '<h1>Hello world!</h1>')

    def test_charfield_render_with_template_with_extra_context(self):
        block = ContextCharBlock(template='tests/blocks/heading_block.html')
        html = block.render("Bonjour le monde!", context={
            'language': 'fr',
        })

        self.assertEqual(html, '<h1 lang="fr">BONJOUR LE MONDE!</h1>')

    def test_charfield_render_form(self):
        block = blocks.CharBlock()
        html = block.render_form("Hello world!")

        self.assertIn('<div class="field char_field widget-text_input">', html)
        self.assertInHTML('<input id="" name="" placeholder="" type="text" value="Hello world!" />', html)

    def test_charfield_render_form_with_prefix(self):
        block = blocks.CharBlock()
        html = block.render_form("Hello world!", prefix='foo')

        self.assertInHTML('<input id="foo" name="foo" placeholder="" type="text" value="Hello world!" />', html)

    def test_charfield_render_form_with_error(self):
        block = blocks.CharBlock()
        html = block.render_form(
            "Hello world!",
            errors=ErrorList([ValidationError("This field is required.")]))

        self.assertIn('This field is required.', html)

    def test_charfield_searchable_content(self):
        block = blocks.CharBlock()
        content = block.get_searchable_content("Hello world!")

        self.assertEqual(content, ["Hello world!"])

    def test_choicefield_render(self):
        class ChoiceBlock(blocks.FieldBlock):
            field = forms.ChoiceField(choices=(
                ('choice-1', "Choice 1"),
                ('choice-2', "Choice 2"),
            ))

        block = ChoiceBlock()
        html = block.render('choice-2')

        self.assertEqual(html, "choice-2")

    def test_choicefield_render_form(self):
        class ChoiceBlock(blocks.FieldBlock):
            field = forms.ChoiceField(choices=(
                ('choice-1', "Choice 1"),
                ('choice-2', "Choice 2"),
            ))

        block = ChoiceBlock()
        html = block.render_form('choice-2')

        self.assertIn('<div class="field choice_field widget-select">', html)
        self.assertTagInHTML('<select id="" name="" placeholder="">', html)
        self.assertInHTML('<option value="choice-1">Choice 1</option>', html)
        self.assertInHTML('<option value="choice-2" selected="selected">Choice 2</option>', html)

    def test_searchable_content(self):
        """
        FieldBlock should not return anything for `get_searchable_content` by
        default. Subclasses are free to override it and provide relevant
        content.
        """
        class CustomBlock(blocks.FieldBlock):
            field = forms.CharField(required=True)
        block = CustomBlock()
        self.assertEqual(block.get_searchable_content("foo bar"), [])

    def test_form_handling_is_independent_of_serialisation(self):
        class Base64EncodingCharBlock(blocks.CharBlock):
            """A CharBlock with a deliberately perverse JSON (de)serialisation format
            so that it visibly blows up if we call to_python / get_prep_value where we shouldn't"""

            def to_python(self, jsonish_value):
                # decode as base64 on the way out of the JSON serialisation
                return base64.b64decode(jsonish_value)

            def get_prep_value(self, native_value):
                # encode as base64 on the way into the JSON serialisation
                return base64.b64encode(native_value)

        block = Base64EncodingCharBlock()
        form_html = block.render_form('hello world', 'title')
        self.assertIn('value="hello world"', form_html)

        value_from_form = block.value_from_datadict({'title': 'hello world'}, {}, 'title')
        self.assertEqual('hello world', value_from_form)

    def test_widget_media(self):
        class CalendarWidget(forms.TextInput):
            @property
            def media(self):
                return forms.Media(
                    css={'all': ('pretty.css',)},
                    js=('animations.js', 'actions.js')
                )

        class CalenderBlock(blocks.FieldBlock):
            def __init__(self, required=True, help_text=None, max_length=None, min_length=None, **kwargs):
                # Set widget to CalenderWidget
                self.field = forms.CharField(
                    required=required,
                    help_text=help_text,
                    max_length=max_length,
                    min_length=min_length,
                    widget=CalendarWidget(),
                )
                super(blocks.FieldBlock, self).__init__(**kwargs)

        block = CalenderBlock()
        self.assertIn('pretty.css', ''.join(block.all_media().render_css()))
        self.assertIn('animations.js', ''.join(block.all_media().render_js()))

    def test_prepare_value_called(self):
        """
        Check that Field.prepare_value is called before sending the value to
        the widget for rendering.

        Actual real-world use case: A Youtube field that produces YoutubeVideo
        instances from IDs, but videos are entered using their full URLs.
        """
        class PrefixWrapper:
            prefix = 'http://example.com/'

            def __init__(self, value):
                self.value = value

            def with_prefix(self):
                return self.prefix + self.value

            @classmethod
            def from_prefixed(cls, value):
                if not value.startswith(cls.prefix):
                    raise ValueError
                return cls(value[len(cls.prefix):])

            def __eq__(self, other):
                return self.value == other.value

        class PrefixField(forms.Field):
            def clean(self, value):
                value = super().clean(value)
                return PrefixWrapper.from_prefixed(value)

            def prepare_value(self, value):
                return value.with_prefix()

        class PrefixedBlock(blocks.FieldBlock):
            def __init__(self, required=True, help_text='', **kwargs):
                super().__init__(**kwargs)
                self.field = PrefixField(required=required, help_text=help_text)

        block = PrefixedBlock()

        # Check that the form value is serialized with a prefix correctly
        value = PrefixWrapper('foo')
        html = block.render_form(value, 'url')
        self.assertInHTML(
            '<input id="url" name="url" placeholder="" type="text" value="{}" />'.format(
                value.with_prefix()),
            html)

        # Check that the value was coerced back to a PrefixValue
        data = {'url': 'http://example.com/bar'}
        new_value = block.clean(block.value_from_datadict(data, {}, 'url'))
        self.assertEqual(new_value, PrefixWrapper('bar'))


class TestIntegerBlock(unittest.TestCase):
    def test_type(self):
        block = blocks.IntegerBlock()
        digit = block.value_from_form(1234)

        self.assertEqual(type(digit), int)

    def test_render(self):
        block = blocks.IntegerBlock()
        digit = block.value_from_form(1234)

        self.assertEqual(digit, 1234)

    def test_render_required_error(self):
        block = blocks.IntegerBlock()

        with self.assertRaises(ValidationError):
            block.clean("")

    def test_render_max_value_validation(self):
        block = blocks.IntegerBlock(max_value=20)

        with self.assertRaises(ValidationError):
            block.clean(25)

    def test_render_min_value_validation(self):
        block = blocks.IntegerBlock(min_value=20)

        with self.assertRaises(ValidationError):
            block.clean(10)


class TestEmailBlock(unittest.TestCase):
    def test_render(self):
        block = blocks.EmailBlock()
        email = block.render("example@email.com")

        self.assertEqual(email, "example@email.com")

    def test_render_required_error(self):
        block = blocks.EmailBlock()

        with self.assertRaises(ValidationError):
            block.clean("")

    def test_format_validation(self):
        block = blocks.EmailBlock()

        with self.assertRaises(ValidationError):
            block.clean("example.email.com")


class TestBlockQuoteBlock(unittest.TestCase):
    def test_render(self):
        block = blocks.BlockQuoteBlock()
        quote = block.render("Now is the time...")

        self.assertEqual(quote, "<blockquote>Now is the time...</blockquote>")


class TestFloatBlock(TestCase):
    def test_type(self):
        block = blocks.FloatBlock()
        block_val = block.value_from_form(float(1.63))
        self.assertEqual(type(block_val), float)

    def test_render(self):
        block = blocks.FloatBlock()
        test_val = float(1.63)
        block_val = block.value_from_form(test_val)
        self.assertEqual(block_val, test_val)

    def test_raises_required_error(self):
        block = blocks.FloatBlock()

        with self.assertRaises(ValidationError):
            block.clean("")

    def test_raises_max_value_validation_error(self):
        block = blocks.FloatBlock(max_value=20)

        with self.assertRaises(ValidationError):
            block.clean('20.01')

    def test_raises_min_value_validation_error(self):
        block = blocks.FloatBlock(min_value=20)

        with self.assertRaises(ValidationError):
            block.clean('19.99')


class TestDecimalBlock(TestCase):
    def test_type(self):
        block = blocks.DecimalBlock()
        block_val = block.value_from_form(Decimal('1.63'))
        self.assertEqual(type(block_val), Decimal)

    def test_render(self):
        block = blocks.DecimalBlock()
        test_val = Decimal(1.63)
        block_val = block.value_from_form(test_val)

        self.assertEqual(block_val, test_val)

    def test_raises_required_error(self):
        block = blocks.DecimalBlock()

        with self.assertRaises(ValidationError):
            block.clean("")

    def test_raises_max_value_validation_error(self):
        block = blocks.DecimalBlock(max_value=20)

        with self.assertRaises(ValidationError):
            block.clean('20.01')

    def test_raises_min_value_validation_error(self):
        block = blocks.DecimalBlock(min_value=20)

        with self.assertRaises(ValidationError):
            block.clean('19.99')


class TestRegexBlock(TestCase):

    def test_render(self):
        block = blocks.RegexBlock(regex=r'^[0-9]{3}$')
        test_val = '123'
        block_val = block.value_from_form(test_val)

        self.assertEqual(block_val, test_val)

    def test_raises_required_error(self):
        block = blocks.RegexBlock(regex=r'^[0-9]{3}$')

        with self.assertRaises(ValidationError) as context:
            block.clean("")

        self.assertIn('This field is required.', context.exception.messages)

    def test_raises_custom_required_error(self):
        test_message = 'Oops, you missed a bit.'
        block = blocks.RegexBlock(regex=r'^[0-9]{3}$', error_messages={
            'required': test_message,
        })

        with self.assertRaises(ValidationError) as context:
            block.clean("")

        self.assertIn(test_message, context.exception.messages)

    def test_raises_validation_error(self):
        block = blocks.RegexBlock(regex=r'^[0-9]{3}$')

        with self.assertRaises(ValidationError) as context:
            block.clean("[/]")

        self.assertIn('Enter a valid value.', context.exception.messages)

    def test_raises_custom_error_message(self):
        test_message = 'Not a valid library card number.'
        block = blocks.RegexBlock(regex=r'^[0-9]{3}$', error_messages={
            'invalid': test_message
        })

        with self.assertRaises(ValidationError) as context:
            block.clean("[/]")

        self.assertIn(test_message, context.exception.messages)

        html = block.render_form(
            "[/]",
            errors=ErrorList([ValidationError(test_message)]))

        self.assertIn(test_message, html)


class TestRichTextBlock(TestCase):
    fixtures = ['test.json']

    def test_get_default_with_fallback_value(self):
        default_value = blocks.RichTextBlock().get_default()
        self.assertIsInstance(default_value, RichText)
        self.assertEqual(default_value.source, '')

    def test_get_default_with_default_none(self):
        default_value = blocks.RichTextBlock(default=None).get_default()
        self.assertIsInstance(default_value, RichText)
        self.assertEqual(default_value.source, '')

    def test_get_default_with_empty_string(self):
        default_value = blocks.RichTextBlock(default='').get_default()
        self.assertIsInstance(default_value, RichText)
        self.assertEqual(default_value.source, '')

    def test_get_default_with_nonempty_string(self):
        default_value = blocks.RichTextBlock(default='<p>foo</p>').get_default()
        self.assertIsInstance(default_value, RichText)
        self.assertEqual(default_value.source, '<p>foo</p>')

    def test_get_default_with_richtext_value(self):
        default_value = blocks.RichTextBlock(default=RichText('<p>foo</p>')).get_default()
        self.assertIsInstance(default_value, RichText)
        self.assertEqual(default_value.source, '<p>foo</p>')

    def test_render(self):
        block = blocks.RichTextBlock()
        value = RichText('<p>Merry <a linktype="page" id="4">Christmas</a>!</p>')
        result = block.render(value)
        self.assertEqual(
            result, '<div class="rich-text"><p>Merry <a href="/events/christmas/">Christmas</a>!</p></div>'
        )

    def test_render_form(self):
        """
        render_form should produce the editor-specific rendition of the rich text value
        (which includes e.g. 'data-linktype' attributes on <a> elements)
        """
        block = blocks.RichTextBlock(editor='hallo')
        value = RichText('<p>Merry <a linktype="page" id="4">Christmas</a>!</p>')
        result = block.render_form(value, prefix='richtext')
        self.assertIn(
            (
                '&lt;p&gt;Merry &lt;a data-linktype=&quot;page&quot; data-id=&quot;4&quot;'
                ' data-parent-id=&quot;3&quot; href=&quot;/events/christmas/&quot;&gt;Christmas&lt;/a&gt;!&lt;/p&gt;'
            ),
            result
        )

    def test_validate_required_richtext_block(self):
        block = blocks.RichTextBlock()

        with self.assertRaises(ValidationError):
            block.clean(RichText(''))

    def test_validate_non_required_richtext_block(self):
        block = blocks.RichTextBlock(required=False)
        result = block.clean(RichText(''))
        self.assertIsInstance(result, RichText)
        self.assertEqual(result.source, '')


class TestChoiceBlock(WagtailTestUtils, SimpleTestCase):
    def setUp(self):
        from django.db.models.fields import BLANK_CHOICE_DASH
        self.blank_choice_dash_label = BLANK_CHOICE_DASH[0][1]

    def test_render_required_choice_block(self):
        block = blocks.ChoiceBlock(choices=[('tea', 'Tea'), ('coffee', 'Coffee')])
        html = block.render_form('coffee', prefix='beverage')
        self.assertTagInHTML('<select id="beverage" name="beverage" placeholder="">', html)
        # blank option should still be rendered for required fields
        # (we may want it as an initial value)
        self.assertIn('<option value="">%s</option>' % self.blank_choice_dash_label, html)
        self.assertIn('<option value="tea">Tea</option>', html)
        self.assertInHTML('<option value="coffee" selected="selected">Coffee</option>', html)

    def test_render_required_choice_block_with_default(self):
        block = blocks.ChoiceBlock(choices=[('tea', 'Tea'), ('coffee', 'Coffee')], default='tea')
        html = block.render_form('coffee', prefix='beverage')
        self.assertTagInHTML('<select id="beverage" name="beverage" placeholder="">', html)
        # blank option should NOT be rendered if default and required are set.
        self.assertNotIn('<option value="">%s</option>' % self.blank_choice_dash_label, html)
        self.assertIn('<option value="tea">Tea</option>', html)
        self.assertInHTML('<option value="coffee" selected="selected">Coffee</option>', html)

    def test_render_required_choice_block_with_callable_choices(self):
        def callable_choices():
            return [('tea', 'Tea'), ('coffee', 'Coffee')]

        block = blocks.ChoiceBlock(choices=callable_choices)
        html = block.render_form('coffee', prefix='beverage')
        self.assertTagInHTML('<select id="beverage" name="beverage" placeholder="">', html)
        # blank option should still be rendered for required fields
        # (we may want it as an initial value)
        self.assertIn('<option value="">%s</option>' % self.blank_choice_dash_label, html)
        self.assertIn('<option value="tea">Tea</option>', html)
        self.assertInHTML('<option value="coffee" selected="selected">Coffee</option>', html)

    def test_validate_required_choice_block(self):
        block = blocks.ChoiceBlock(choices=[('tea', 'Tea'), ('coffee', 'Coffee')])
        self.assertEqual(block.clean('coffee'), 'coffee')

        with self.assertRaises(ValidationError):
            block.clean('whisky')

        with self.assertRaises(ValidationError):
            block.clean('')

        with self.assertRaises(ValidationError):
            block.clean(None)

    def test_render_non_required_choice_block(self):
        block = blocks.ChoiceBlock(choices=[('tea', 'Tea'), ('coffee', 'Coffee')], required=False)
        html = block.render_form('coffee', prefix='beverage')
        self.assertTagInHTML('<select id="beverage" name="beverage" placeholder="">', html)
        self.assertIn('<option value="">%s</option>' % self.blank_choice_dash_label, html)
        self.assertIn('<option value="tea">Tea</option>', html)
        self.assertInHTML('<option value="coffee" selected="selected">Coffee</option>', html)

    def test_render_non_required_choice_block_with_callable_choices(self):
        def callable_choices():
            return [('tea', 'Tea'), ('coffee', 'Coffee')]

        block = blocks.ChoiceBlock(choices=callable_choices, required=False)
        html = block.render_form('coffee', prefix='beverage')
        self.assertTagInHTML('<select id="beverage" name="beverage" placeholder="">', html)
        self.assertIn('<option value="">%s</option>' % self.blank_choice_dash_label, html)
        self.assertIn('<option value="tea">Tea</option>', html)
        self.assertInHTML('<option value="coffee" selected="selected">Coffee</option>', html)

    def test_validate_non_required_choice_block(self):
        block = blocks.ChoiceBlock(choices=[('tea', 'Tea'), ('coffee', 'Coffee')], required=False)
        self.assertEqual(block.clean('coffee'), 'coffee')

        with self.assertRaises(ValidationError):
            block.clean('whisky')

        self.assertEqual(block.clean(''), '')
        self.assertEqual(block.clean(None), '')

    def test_render_choice_block_with_existing_blank_choice(self):
        block = blocks.ChoiceBlock(
            choices=[('tea', 'Tea'), ('coffee', 'Coffee'), ('', 'No thanks')],
            required=False)
        html = block.render_form(None, prefix='beverage')
        self.assertTagInHTML('<select id="beverage" name="beverage" placeholder="">', html)
        self.assertNotIn('<option value="">%s</option>' % self.blank_choice_dash_label, html)
        self.assertInHTML('<option value="" selected="selected">No thanks</option>', html)
        self.assertIn('<option value="tea">Tea</option>', html)
        self.assertInHTML('<option value="coffee">Coffee</option>', html)

    def test_render_choice_block_with_existing_blank_choice_and_with_callable_choices(self):
        def callable_choices():
            return [('tea', 'Tea'), ('coffee', 'Coffee'), ('', 'No thanks')]

        block = blocks.ChoiceBlock(
            choices=callable_choices,
            required=False)
        html = block.render_form(None, prefix='beverage')
        self.assertTagInHTML('<select id="beverage" name="beverage" placeholder="">', html)
        self.assertNotIn('<option value="">%s</option>' % self.blank_choice_dash_label, html)
        self.assertInHTML('<option value="" selected="selected">No thanks</option>', html)
        self.assertIn('<option value="tea">Tea</option>', html)
        self.assertIn('<option value="coffee">Coffee</option>', html)

    def test_named_groups_without_blank_option(self):
        block = blocks.ChoiceBlock(
            choices=[
                ('Alcoholic', [
                    ('gin', 'Gin'),
                    ('whisky', 'Whisky'),
                ]),
                ('Non-alcoholic', [
                    ('tea', 'Tea'),
                    ('coffee', 'Coffee'),
                ]),
            ])

        # test rendering with the blank option selected
        html = block.render_form(None, prefix='beverage')
        self.assertTagInHTML('<select id="beverage" name="beverage" placeholder="">', html)
        self.assertInHTML('<option value="" selected="selected">%s</option>' % self.blank_choice_dash_label, html)
        self.assertIn('<optgroup label="Alcoholic">', html)
        self.assertIn('<option value="tea">Tea</option>', html)

        # test rendering with a non-blank option selected
        html = block.render_form('tea', prefix='beverage')
        self.assertTagInHTML('<select id="beverage" name="beverage" placeholder="">', html)
        self.assertIn('<option value="">%s</option>' % self.blank_choice_dash_label, html)
        self.assertIn('<optgroup label="Alcoholic">', html)
        self.assertInHTML('<option value="tea" selected="selected">Tea</option>', html)

    def test_named_groups_with_blank_option(self):
        block = blocks.ChoiceBlock(
            choices=[
                ('Alcoholic', [
                    ('gin', 'Gin'),
                    ('whisky', 'Whisky'),
                ]),
                ('Non-alcoholic', [
                    ('tea', 'Tea'),
                    ('coffee', 'Coffee'),
                ]),
                ('Not thirsty', [
                    ('', 'No thanks')
                ]),
            ],
            required=False)

        # test rendering with the blank option selected
        html = block.render_form(None, prefix='beverage')
        self.assertTagInHTML('<select id="beverage" name="beverage" placeholder="">', html)
        self.assertNotIn('<option value="">%s</option>' % self.blank_choice_dash_label, html)
        self.assertNotInHTML('<option value="" selected="selected">%s</option>' % self.blank_choice_dash_label, html)
        self.assertIn('<optgroup label="Alcoholic">', html)
        self.assertIn('<option value="tea">Tea</option>', html)
        self.assertInHTML('<option value="" selected="selected">No thanks</option>', html)

        # test rendering with a non-blank option selected
        html = block.render_form('tea', prefix='beverage')
        self.assertTagInHTML('<select id="beverage" name="beverage" placeholder="">', html)
        self.assertNotIn('<option value="">%s</option>' % self.blank_choice_dash_label, html)
        self.assertNotInHTML('<option value="" selected="selected">%s</option>' % self.blank_choice_dash_label, html)
        self.assertIn('<optgroup label="Alcoholic">', html)
        self.assertInHTML('<option value="tea" selected="selected">Tea</option>', html)

    def test_subclassing(self):
        class BeverageChoiceBlock(blocks.ChoiceBlock):
            choices = [
                ('tea', 'Tea'),
                ('coffee', 'Coffee'),
            ]

        block = BeverageChoiceBlock(required=False)
        html = block.render_form('tea', prefix='beverage')
        self.assertTagInHTML('<select id="beverage" name="beverage" placeholder="">', html)
        self.assertInHTML('<option value="tea" selected="selected">Tea</option>', html)

        # subclasses of ChoiceBlock should deconstruct to a basic ChoiceBlock for migrations
        self.assertEqual(
            block.deconstruct(),
            (
                'wagtail.core.blocks.ChoiceBlock',
                [],
                {
                    'choices': [('tea', 'Tea'), ('coffee', 'Coffee')],
                    'required': False,
                },
            )
        )

    def test_searchable_content(self):
        block = blocks.ChoiceBlock(choices=[
            ('choice-1', "Choice 1"),
            ('choice-2', "Choice 2"),
        ])
        self.assertEqual(block.get_searchable_content("choice-1"),
                         ["Choice 1"])

    def test_searchable_content_with_callable_choices(self):
        def callable_choices():
            return [
                ('choice-1', "Choice 1"),
                ('choice-2', "Choice 2"),
            ]

        block = blocks.ChoiceBlock(choices=callable_choices)
        self.assertEqual(block.get_searchable_content("choice-1"),
                         ["Choice 1"])

    def test_optgroup_searchable_content(self):
        block = blocks.ChoiceBlock(choices=[
            ('Section 1', [
                ('1-1', "Block 1"),
                ('1-2', "Block 2"),
            ]),
            ('Section 2', [
                ('2-1', "Block 1"),
                ('2-2', "Block 2"),
            ]),
        ])
        self.assertEqual(block.get_searchable_content("2-2"),
                         ["Section 2", "Block 2"])

    def test_invalid_searchable_content(self):
        block = blocks.ChoiceBlock(choices=[
            ('one', 'One'),
            ('two', 'Two'),
        ])
        self.assertEqual(block.get_searchable_content('three'), [])

    def test_searchable_content_with_lazy_translation(self):
        block = blocks.ChoiceBlock(choices=[
            ('choice-1', __("Choice 1")),
            ('choice-2', __("Choice 2")),
        ])
        result = block.get_searchable_content("choice-1")
        # result must survive JSON (de)serialisation, which is not the case for
        # lazy translation objects
        result = json.loads(json.dumps(result))
        self.assertEqual(result, ["Choice 1"])

    def test_optgroup_searchable_content_with_lazy_translation(self):
        block = blocks.ChoiceBlock(choices=[
            (__('Section 1'), [
                ('1-1', __("Block 1")),
                ('1-2', __("Block 2")),
            ]),
            (__('Section 2'), [
                ('2-1', __("Block 1")),
                ('2-2', __("Block 2")),
            ]),
        ])
        result = block.get_searchable_content("2-2")
        # result must survive JSON (de)serialisation, which is not the case for
        # lazy translation objects
        result = json.loads(json.dumps(result))
        self.assertEqual(result, ["Section 2", "Block 2"])

    def test_deconstruct_with_callable_choices(self):
        def callable_choices():
            return [
                ('tea', 'Tea'),
                ('coffee', 'Coffee'),
            ]

        block = blocks.ChoiceBlock(choices=callable_choices, required=False)
        html = block.render_form('tea', prefix='beverage')

        self.assertTagInHTML('<select id="beverage" name="beverage" placeholder="">', html)
        self.assertInHTML('<option value="tea" selected="selected">Tea</option>', html)

        self.assertEqual(
            block.deconstruct(),
            (
                'wagtail.core.blocks.ChoiceBlock',
                [],
                {
                    'choices': callable_choices,
                    'required': False,
                },
            )
        )


class TestRawHTMLBlock(unittest.TestCase):
    def test_get_default_with_fallback_value(self):
        default_value = blocks.RawHTMLBlock().get_default()
        self.assertEqual(default_value, '')
        self.assertIsInstance(default_value, SafeData)

    def test_get_default_with_none(self):
        default_value = blocks.RawHTMLBlock(default=None).get_default()
        self.assertEqual(default_value, '')
        self.assertIsInstance(default_value, SafeData)

    def test_get_default_with_empty_string(self):
        default_value = blocks.RawHTMLBlock(default='').get_default()
        self.assertEqual(default_value, '')
        self.assertIsInstance(default_value, SafeData)

    def test_get_default_with_nonempty_string(self):
        default_value = blocks.RawHTMLBlock(default='<blink>BÖÖM</blink>').get_default()
        self.assertEqual(default_value, '<blink>BÖÖM</blink>')
        self.assertIsInstance(default_value, SafeData)

    def test_serialize(self):
        block = blocks.RawHTMLBlock()
        result = block.get_prep_value(mark_safe('<blink>BÖÖM</blink>'))
        self.assertEqual(result, '<blink>BÖÖM</blink>')
        self.assertNotIsInstance(result, SafeData)

    def test_deserialize(self):
        block = blocks.RawHTMLBlock()
        result = block.to_python('<blink>BÖÖM</blink>')
        self.assertEqual(result, '<blink>BÖÖM</blink>')
        self.assertIsInstance(result, SafeData)

    def test_render(self):
        block = blocks.RawHTMLBlock()
        result = block.render(mark_safe('<blink>BÖÖM</blink>'))
        self.assertEqual(result, '<blink>BÖÖM</blink>')
        self.assertIsInstance(result, SafeData)

    def test_render_form(self):
        block = blocks.RawHTMLBlock()
        result = block.render_form(mark_safe('<blink>BÖÖM</blink>'), prefix='rawhtml')
        self.assertIn('<textarea ', result)
        self.assertIn('name="rawhtml"', result)
        self.assertIn('&lt;blink&gt;BÖÖM&lt;/blink&gt;', result)

    def test_form_response(self):
        block = blocks.RawHTMLBlock()
        result = block.value_from_datadict({'rawhtml': '<blink>BÖÖM</blink>'}, {}, prefix='rawhtml')
        self.assertEqual(result, '<blink>BÖÖM</blink>')
        self.assertIsInstance(result, SafeData)

    def test_value_omitted_from_data(self):
        block = blocks.RawHTMLBlock()
        self.assertFalse(block.value_omitted_from_data({'rawhtml': 'ohai'}, {}, 'rawhtml'))
        self.assertFalse(block.value_omitted_from_data({'rawhtml': ''}, {}, 'rawhtml'))
        self.assertTrue(block.value_omitted_from_data({'nothing-here': 'nope'}, {}, 'rawhtml'))

    def test_clean_required_field(self):
        block = blocks.RawHTMLBlock()
        result = block.clean(mark_safe('<blink>BÖÖM</blink>'))
        self.assertEqual(result, '<blink>BÖÖM</blink>')
        self.assertIsInstance(result, SafeData)

        with self.assertRaises(ValidationError):
            block.clean(mark_safe(''))

    def test_clean_nonrequired_field(self):
        block = blocks.RawHTMLBlock(required=False)
        result = block.clean(mark_safe('<blink>BÖÖM</blink>'))
        self.assertEqual(result, '<blink>BÖÖM</blink>')
        self.assertIsInstance(result, SafeData)

        result = block.clean(mark_safe(''))
        self.assertEqual(result, '')
        self.assertIsInstance(result, SafeData)


class TestMeta(unittest.TestCase):
    def test_set_template_with_meta(self):
        class HeadingBlock(blocks.CharBlock):
            class Meta:
                template = 'heading.html'

        block = HeadingBlock()
        self.assertEqual(block.meta.template, 'heading.html')

    def test_set_template_with_constructor(self):
        block = blocks.CharBlock(template='heading.html')
        self.assertEqual(block.meta.template, 'heading.html')

    def test_set_template_with_constructor_overrides_meta(self):
        class HeadingBlock(blocks.CharBlock):
            class Meta:
                template = 'heading.html'

        block = HeadingBlock(template='subheading.html')
        self.assertEqual(block.meta.template, 'subheading.html')

    def test_meta_nested_inheritance(self):
        """
        Check that having a multi-level inheritance chain works
        """
        class HeadingBlock(blocks.CharBlock):
            class Meta:
                template = 'heading.html'
                test = 'Foo'

        class SubHeadingBlock(HeadingBlock):
            class Meta:
                template = 'subheading.html'

        block = SubHeadingBlock()
        self.assertEqual(block.meta.template, 'subheading.html')
        self.assertEqual(block.meta.test, 'Foo')

    def test_meta_multi_inheritance(self):
        """
        Check that multi-inheritance and Meta classes work together
        """
        class LeftBlock(blocks.CharBlock):
            class Meta:
                template = 'template.html'
                clash = 'the band'
                label = 'Left block'

        class RightBlock(blocks.CharBlock):
            class Meta:
                default = 'hello'
                clash = 'the album'
                label = 'Right block'

        class ChildBlock(LeftBlock, RightBlock):
            class Meta:
                label = 'Child block'

        block = ChildBlock()
        # These should be directly inherited from the LeftBlock/RightBlock
        self.assertEqual(block.meta.template, 'template.html')
        self.assertEqual(block.meta.default, 'hello')

        # This should be inherited from the LeftBlock, solving the collision,
        # as LeftBlock comes first
        self.assertEqual(block.meta.clash, 'the band')

        # This should come from ChildBlock itself, ignoring the label on
        # LeftBlock/RightBlock
        self.assertEqual(block.meta.label, 'Child block')


class TestStructBlock(SimpleTestCase):
    def test_initialisation(self):
        block = blocks.StructBlock([
            ('title', blocks.CharBlock()),
            ('link', blocks.URLBlock()),
        ])

        self.assertEqual(list(block.child_blocks.keys()), ['title', 'link'])

    def test_initialisation_from_subclass(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            link = blocks.URLBlock()

        block = LinkBlock()

        self.assertEqual(list(block.child_blocks.keys()), ['title', 'link'])

    def test_initialisation_from_subclass_with_extra(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            link = blocks.URLBlock()

        block = LinkBlock([
            ('classname', blocks.CharBlock())
        ])

        self.assertEqual(list(block.child_blocks.keys()), ['title', 'link', 'classname'])

    def test_initialisation_with_multiple_subclassses(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            link = blocks.URLBlock()

        class StyledLinkBlock(LinkBlock):
            classname = blocks.CharBlock()

        block = StyledLinkBlock()

        self.assertEqual(list(block.child_blocks.keys()), ['title', 'link', 'classname'])

    def test_initialisation_with_mixins(self):
        """
        The order of fields of classes with multiple parent classes is slightly
        surprising at first. Child fields are inherited in a bottom-up order,
        by traversing the MRO in reverse. In the example below,
        ``StyledLinkBlock`` will have an MRO of::

            [StyledLinkBlock, StylingMixin, LinkBlock, StructBlock, ...]

        This will result in ``classname`` appearing *after* ``title`` and
        ``link`` in ``StyleLinkBlock`.child_blocks`, even though
        ``StylingMixin`` appeared before ``LinkBlock``.
        """
        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            link = blocks.URLBlock()

        class StylingMixin(blocks.StructBlock):
            classname = blocks.CharBlock()

        class StyledLinkBlock(StylingMixin, LinkBlock):
            source = blocks.CharBlock()

        block = StyledLinkBlock()

        self.assertEqual(list(block.child_blocks.keys()),
                         ['title', 'link', 'classname', 'source'])

    def test_render(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            link = blocks.URLBlock()

        block = LinkBlock()
        html = block.render(block.to_python({
            'title': "Wagtail site",
            'link': 'http://www.wagtail.io',
        }))
        expected_html = '\n'.join([
            '<dl>',
            '<dt>title</dt>',
            '<dd>Wagtail site</dd>',
            '<dt>link</dt>',
            '<dd>http://www.wagtail.io</dd>',
            '</dl>',
        ])

        self.assertHTMLEqual(html, expected_html)

    def test_get_api_representation_calls_same_method_on_fields_with_context(self):
        """
        The get_api_representation method of a StructBlock should invoke
        the block's get_api_representation method on each field and the
        context should be passed on.
        """
        class ContextBlock(blocks.CharBlock):
            def get_api_representation(self, value, context=None):
                return context[value]

        class AuthorBlock(blocks.StructBlock):
            language = ContextBlock()
            author = ContextBlock()

        block = AuthorBlock()
        api_representation = block.get_api_representation(
            {
                'language': 'en',
                'author': 'wagtail',
            },
            context={
                'en': 'English',
                'wagtail': 'Wagtail!'
            }
        )

        self.assertDictEqual(
            api_representation, {
                'language': 'English',
                'author': 'Wagtail!'
            }
        )

    def test_render_unknown_field(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            link = blocks.URLBlock()

        block = LinkBlock()
        html = block.render(block.to_python({
            'title': "Wagtail site",
            'link': 'http://www.wagtail.io',
            'image': 10,
        }))

        self.assertIn('<dt>title</dt>', html)
        self.assertIn('<dd>Wagtail site</dd>', html)
        self.assertIn('<dt>link</dt>', html)
        self.assertIn('<dd>http://www.wagtail.io</dd>', html)

        # Don't render the extra item
        self.assertNotIn('<dt>image</dt>', html)

    def test_render_bound_block(self):
        # the string representation of a bound block should be the value as rendered by
        # the associated block
        class SectionBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            body = blocks.RichTextBlock()

        block = SectionBlock()
        struct_value = block.to_python({
            'title': 'hello',
            'body': '<b>world</b>',
        })
        body_bound_block = struct_value.bound_blocks['body']
        expected = '<div class="rich-text"><b>world</b></div>'
        self.assertEqual(str(body_bound_block), expected)

    def test_get_form_context(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            link = blocks.URLBlock()

        block = LinkBlock()
        context = block.get_form_context(block.to_python({
            'title': "Wagtail site",
            'link': 'http://www.wagtail.io',
        }), prefix='mylink')

        self.assertTrue(isinstance(context['children'], collections.OrderedDict))
        self.assertEqual(len(context['children']), 2)
        self.assertTrue(isinstance(context['children']['title'], blocks.BoundBlock))
        self.assertEqual(context['children']['title'].value, "Wagtail site")
        self.assertTrue(isinstance(context['children']['link'], blocks.BoundBlock))
        self.assertEqual(context['children']['link'].value, 'http://www.wagtail.io')
        self.assertEqual(context['block_definition'], block)
        self.assertEqual(context['prefix'], 'mylink')

    def test_render_form(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock(required=False)
            link = blocks.URLBlock(required=False)

        block = LinkBlock()
        html = block.render_form(block.to_python({
            'title': "Wagtail site",
            'link': 'http://www.wagtail.io',
        }), prefix='mylink')

        self.assertIn('<div class="struct-block">', html)
        self.assertIn('<div class="field char_field widget-text_input fieldname-title">', html)
        self.assertIn('<label for="mylink-title">Title:</label>', html)
        self.assertInHTML(
            '<input id="mylink-title" name="mylink-title" placeholder="Title" type="text" value="Wagtail site" />', html
        )
        self.assertIn('<div class="field url_field widget-url_input fieldname-link">', html)
        self.assertInHTML(
            (
                '<input id="mylink-link" name="mylink-link" placeholder="Link"'
                ' type="url" value="http://www.wagtail.io" />'
            ),
            html
        )
        self.assertNotIn('<li class="required">', html)

    def test_render_required_field_indicator(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            link = blocks.URLBlock(required=True)

        block = LinkBlock()
        html = block.render_form(block.to_python({
            'title': "Wagtail site",
            'link': 'http://www.wagtail.io',
        }), prefix='mylink')

        self.assertIn('<li class="required">', html)

    def test_render_form_unknown_field(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            link = blocks.URLBlock()

        block = LinkBlock()
        html = block.render_form(block.to_python({
            'title': "Wagtail site",
            'link': 'http://www.wagtail.io',
            'image': 10,
        }), prefix='mylink')

        self.assertInHTML(
            (
                '<input id="mylink-title" name="mylink-title" placeholder="Title"'
                ' type="text" value="Wagtail site" />'
            ),
            html
        )
        self.assertInHTML(
            (
                '<input id="mylink-link" name="mylink-link" placeholder="Link" type="url"'
                ' value="http://www.wagtail.io" />'
            ),
            html
        )

        # Don't render the extra field
        self.assertNotIn('mylink-image', html)

    def test_render_form_uses_default_value(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock(default="Torchbox")
            link = blocks.URLBlock(default="http://www.torchbox.com")

        block = LinkBlock()
        html = block.render_form(block.to_python({}), prefix='mylink')

        self.assertInHTML(
            '<input id="mylink-title" name="mylink-title" placeholder="Title" type="text" value="Torchbox" />', html
        )
        self.assertInHTML(
            (
                '<input id="mylink-link" name="mylink-link" placeholder="Link"'
                ' type="url" value="http://www.torchbox.com" />'
            ),
            html
        )

    def test_render_form_with_help_text(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            link = blocks.URLBlock()

            class Meta:
                help_text = "Self-promotion is encouraged"

        block = LinkBlock()
        html = block.render_form(block.to_python({
            'title': "Wagtail site",
            'link': 'http://www.wagtail.io',
        }), prefix='mylink')

        self.assertIn('<div class="sequence-member__help help"><span class="icon-help-inverse" aria-hidden="true"></span>Self-promotion is encouraged</div>', html)

        # check it can be overridden in the block constructor
        block = LinkBlock(help_text="Self-promotion is discouraged")
        html = block.render_form(block.to_python({
            'title': "Wagtail site",
            'link': 'http://www.wagtail.io',
        }), prefix='mylink')

        self.assertIn('<div class="sequence-member__help help"><span class="icon-help-inverse" aria-hidden="true"></span>Self-promotion is discouraged</div>', html)

    def test_media_inheritance(self):
        class ScriptedCharBlock(blocks.CharBlock):
            media = forms.Media(js=['scripted_char_block.js'])

        class LinkBlock(blocks.StructBlock):
            title = ScriptedCharBlock(default="Torchbox")
            link = blocks.URLBlock(default="http://www.torchbox.com")

        block = LinkBlock()
        self.assertIn('scripted_char_block.js', ''.join(block.all_media().render_js()))

    def test_html_declaration_inheritance(self):
        class CharBlockWithDeclarations(blocks.CharBlock):
            def html_declarations(self):
                return '<script type="text/x-html-template">hello world</script>'

        class LinkBlock(blocks.StructBlock):
            title = CharBlockWithDeclarations(default="Torchbox")
            link = blocks.URLBlock(default="http://www.torchbox.com")

        block = LinkBlock()
        self.assertIn('<script type="text/x-html-template">hello world</script>', block.all_html_declarations())

    def test_searchable_content(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            link = blocks.URLBlock()

        block = LinkBlock()
        content = block.get_searchable_content(block.to_python({
            'title': "Wagtail site",
            'link': 'http://www.wagtail.io',
        }))

        self.assertEqual(content, ["Wagtail site"])

    def test_value_from_datadict(self):
        block = blocks.StructBlock([
            ('title', blocks.CharBlock()),
            ('link', blocks.URLBlock()),
        ])

        struct_val = block.value_from_datadict({
            'mylink-title': "Torchbox",
            'mylink-link': "http://www.torchbox.com"
        }, {}, 'mylink')

        self.assertEqual(struct_val['title'], "Torchbox")
        self.assertEqual(struct_val['link'], "http://www.torchbox.com")
        self.assertTrue(isinstance(struct_val, blocks.StructValue))
        self.assertTrue(isinstance(struct_val.bound_blocks['link'].block, blocks.URLBlock))

    def test_value_omitted_from_data(self):
        block = blocks.StructBlock([
            ('title', blocks.CharBlock()),
            ('link', blocks.URLBlock()),
        ])

        # overall value is considered present in the form if any sub-field is present
        self.assertFalse(block.value_omitted_from_data({'mylink-title': 'Torchbox'}, {}, 'mylink'))
        self.assertTrue(block.value_omitted_from_data({'nothing-here': 'nope'}, {}, 'mylink'))

    def test_default_is_returned_as_structvalue(self):
        """When returning the default value of a StructBlock (e.g. because it's
        a child of another StructBlock, and the outer value is missing that key)
        we should receive it as a StructValue, not just a plain dict"""
        class PersonBlock(blocks.StructBlock):
            first_name = blocks.CharBlock()
            surname = blocks.CharBlock()

        class EventBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            guest_speaker = PersonBlock(default={'first_name': 'Ed', 'surname': 'Balls'})

        event_block = EventBlock()

        event = event_block.to_python({'title': 'Birthday party'})

        self.assertEqual(event['guest_speaker']['first_name'], 'Ed')
        self.assertTrue(isinstance(event['guest_speaker'], blocks.StructValue))

    def test_clean(self):
        block = blocks.StructBlock([
            ('title', blocks.CharBlock()),
            ('link', blocks.URLBlock()),
        ])

        value = block.to_python({'title': 'Torchbox', 'link': 'http://www.torchbox.com/'})
        clean_value = block.clean(value)
        self.assertTrue(isinstance(clean_value, blocks.StructValue))
        self.assertEqual(clean_value['title'], 'Torchbox')

        value = block.to_python({'title': 'Torchbox', 'link': 'not a url'})
        with self.assertRaises(ValidationError):
            block.clean(value)

    def test_bound_blocks_are_available_on_template(self):
        """
        Test that we are able to use value.bound_blocks within templates
        to access a child block's own HTML rendering
        """
        block = SectionBlock()
        value = block.to_python({'title': 'Hello', 'body': '<i>italic</i> world'})
        result = block.render(value)
        self.assertEqual(result, """<h1>Hello</h1><div class="rich-text"><i>italic</i> world</div>""")

    def test_render_block_with_extra_context(self):
        block = SectionBlock()
        value = block.to_python({'title': 'Bonjour', 'body': 'monde <i>italique</i>'})
        result = block.render(value, context={'language': 'fr'})
        self.assertEqual(result, """<h1 lang="fr">Bonjour</h1><div class="rich-text">monde <i>italique</i></div>""")

    def test_render_structvalue(self):
        """
        The HTML representation of a StructValue should use the block's template
        """
        block = SectionBlock()
        value = block.to_python({'title': 'Hello', 'body': '<i>italic</i> world'})
        result = value.__html__()
        self.assertEqual(result, """<h1>Hello</h1><div class="rich-text"><i>italic</i> world</div>""")

        # value.render_as_block() should be equivalent to value.__html__()
        result = value.render_as_block()
        self.assertEqual(result, """<h1>Hello</h1><div class="rich-text"><i>italic</i> world</div>""")

    def test_str_structvalue(self):
        """
        The str() representation of a StructValue should NOT render the template, as that's liable
        to cause an infinite loop if any debugging / logging code attempts to log the fact that
        it rendered a template with this object in the context:
        https://github.com/wagtail/wagtail/issues/2874
        https://github.com/jazzband/django-debug-toolbar/issues/950
        """
        block = SectionBlock()
        value = block.to_python({'title': 'Hello', 'body': '<i>italic</i> world'})
        result = str(value)
        self.assertNotIn('<h1>', result)
        # The expected rendering should correspond to the native representation of an OrderedDict:
        # "StructValue([('title', u'Hello'), ('body', <wagtail.core.rich_text.RichText object at 0xb12d5eed>)])"
        # - give or take some quoting differences between Python versions
        self.assertIn('StructValue', result)
        self.assertIn('title', result)
        self.assertIn('Hello', result)

    def test_render_structvalue_with_extra_context(self):
        block = SectionBlock()
        value = block.to_python({'title': 'Bonjour', 'body': 'monde <i>italique</i>'})
        result = value.render_as_block(context={'language': 'fr'})
        self.assertEqual(result, """<h1 lang="fr">Bonjour</h1><div class="rich-text">monde <i>italique</i></div>""")


class TestStructBlockWithCustomStructValue(SimpleTestCase):

    def test_initialisation(self):

        class CustomStructValue(blocks.StructValue):
            def joined(self):
                return self.get('title', '') + self.get('link', '')

        block = blocks.StructBlock([
            ('title', blocks.CharBlock()),
            ('link', blocks.URLBlock()),
        ], value_class=CustomStructValue)

        self.assertEqual(list(block.child_blocks.keys()), ['title', 'link'])

        block_value = block.to_python({'title': 'Birthday party', 'link': 'https://myparty.co.uk'})
        self.assertIsInstance(block_value, CustomStructValue)

        default_value = block.get_default()
        self.assertIsInstance(default_value, CustomStructValue)

        value_from_datadict = block.value_from_datadict({
            'mylink-title': "Torchbox",
            'mylink-link': "http://www.torchbox.com"
        }, {}, 'mylink')

        self.assertIsInstance(value_from_datadict, CustomStructValue)

        value = block.to_python({'title': 'Torchbox', 'link': 'http://www.torchbox.com/'})
        clean_value = block.clean(value)
        self.assertTrue(isinstance(clean_value, CustomStructValue))
        self.assertEqual(clean_value['title'], 'Torchbox')

        value = block.to_python({'title': 'Torchbox', 'link': 'not a url'})
        with self.assertRaises(ValidationError):
            block.clean(value)


    def test_initialisation_from_subclass(self):

        class LinkStructValue(blocks.StructValue):
            def url(self):
                return self.get('page') or self.get('link')

        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            page = blocks.PageChooserBlock(required=False)
            link = blocks.URLBlock(required=False)

            class Meta:
                value_class = LinkStructValue

        block = LinkBlock()

        self.assertEqual(list(block.child_blocks.keys()), ['title', 'page', 'link'])

        block_value = block.to_python({'title': 'Website', 'link': 'https://website.com'})
        self.assertIsInstance(block_value, LinkStructValue)

        default_value = block.get_default()
        self.assertIsInstance(default_value, LinkStructValue)


    def test_initialisation_with_multiple_subclassses(self):
        class LinkStructValue(blocks.StructValue):
            def url(self):
                return self.get('page') or self.get('link')

        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            page = blocks.PageChooserBlock(required=False)
            link = blocks.URLBlock(required=False)

            class Meta:
                value_class = LinkStructValue

        class StyledLinkBlock(LinkBlock):
            classname = blocks.CharBlock()

        block = StyledLinkBlock()

        self.assertEqual(list(block.child_blocks.keys()), ['title', 'page', 'link', 'classname'])

        value_from_datadict = block.value_from_datadict({
            'queen-title': "Torchbox",
            'queen-link': "http://www.torchbox.com",
            'queen-classname': "fullsize",
        }, {}, 'queen')

        self.assertIsInstance(value_from_datadict, LinkStructValue)

    def test_initialisation_with_mixins(self):
        class LinkStructValue(blocks.StructValue):
            pass

        class StylingMixinStructValue(blocks.StructValue):
            pass

        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            link = blocks.URLBlock()

            class Meta:
                value_class = LinkStructValue

        class StylingMixin(blocks.StructBlock):
            classname = blocks.CharBlock()

        class StyledLinkBlock(StylingMixin, LinkBlock):
            source = blocks.CharBlock()

        block = StyledLinkBlock()

        self.assertEqual(list(block.child_blocks.keys()),
                         ['title', 'link', 'classname', 'source'])

        block_value = block.to_python({
            'title': 'Website', 'link': 'https://website.com',
            'source': 'google', 'classname': 'full-size',
        })
        self.assertIsInstance(block_value, LinkStructValue)


    def test_value_property(self):

        class SectionStructValue(blocks.StructValue):
            @property
            def foo(self):
                return 'bar %s' % self.get('title', '')

        class SectionBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            body = blocks.RichTextBlock()

            class Meta:
                value_class = SectionStructValue

        block = SectionBlock()
        struct_value = block.to_python({'title': 'hello', 'body': '<b>world</b>'})
        value = struct_value.foo
        self.assertEqual(value, 'bar hello')

    def test_render_with_template(self):

        class SectionStructValue(blocks.StructValue):
            def title_with_suffix(self):
                title = self.get('title')
                if title:
                    return 'SUFFIX %s' % title
                return 'EMPTY TITLE'

        class SectionBlock(blocks.StructBlock):
            title = blocks.CharBlock(required=False)

            class Meta:
                value_class = SectionStructValue

        block = SectionBlock(template='tests/blocks/struct_block_custom_value.html')
        struct_value = block.to_python({'title': 'hello'})
        html = block.render(struct_value)
        self.assertEqual(html, '<div>SUFFIX hello</div>\n')

        struct_value = block.to_python({})
        html = block.render(struct_value)
        self.assertEqual(html, '<div>EMPTY TITLE</div>\n')


class TestListBlock(WagtailTestUtils, SimpleTestCase):
    def test_initialise_with_class(self):
        block = blocks.ListBlock(blocks.CharBlock)

        # Child block should be initialised for us
        self.assertIsInstance(block.child_block, blocks.CharBlock)

    def test_initialise_with_instance(self):
        child_block = blocks.CharBlock()
        block = blocks.ListBlock(child_block)

        self.assertEqual(block.child_block, child_block)

    def render(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            link = blocks.URLBlock()

        block = blocks.ListBlock(LinkBlock())
        return block.render([
            {
                'title': "Wagtail",
                'link': 'http://www.wagtail.io',
            },
            {
                'title': "Django",
                'link': 'http://www.djangoproject.com',
            },
        ])

    def test_render_uses_ul(self):
        html = self.render()

        self.assertIn('<ul>', html)
        self.assertIn('</ul>', html)

    def test_render_uses_li(self):
        html = self.render()

        self.assertIn('<li>', html)
        self.assertIn('</li>', html)

    def test_render_calls_block_render_on_children(self):
        """
        The default rendering of a ListBlock should invoke the block's render method
        on each child, rather than just outputting the child value as a string.
        """
        block = blocks.ListBlock(
            blocks.CharBlock(template='tests/blocks/heading_block.html')
        )
        html = block.render(["Hello world!", "Goodbye world!"])

        self.assertIn('<h1>Hello world!</h1>', html)
        self.assertIn('<h1>Goodbye world!</h1>', html)

    def test_render_passes_context_to_children(self):
        """
        Template context passed to the render method should be passed on
        to the render method of the child block.
        """
        block = blocks.ListBlock(
            blocks.CharBlock(template='tests/blocks/heading_block.html')
        )
        html = block.render(["Bonjour le monde!", "Au revoir le monde!"], context={
            'language': 'fr',
        })

        self.assertIn('<h1 lang="fr">Bonjour le monde!</h1>', html)
        self.assertIn('<h1 lang="fr">Au revoir le monde!</h1>', html)

    def test_get_api_representation_calls_same_method_on_children_with_context(self):
        """
        The get_api_representation method of a ListBlock should invoke
        the block's get_api_representation method on each child and
        the context should be passed on.
        """
        class ContextBlock(blocks.CharBlock):
            def get_api_representation(self, value, context=None):
                return context[value]

        block = blocks.ListBlock(
            ContextBlock()
        )
        api_representation = block.get_api_representation(["en", "fr"], context={
            'en': 'Hello world!',
            'fr': 'Bonjour le monde!'
        })

        self.assertEqual(
            api_representation, ['Hello world!', 'Bonjour le monde!']
        )

    def render_form(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            link = blocks.URLBlock()

        block = blocks.ListBlock(LinkBlock)

        html = block.render_form([
            {
                'title': "Wagtail",
                'link': 'http://www.wagtail.io',
            },
            {
                'title': "Django",
                'link': 'http://www.djangoproject.com',
            },
        ], prefix='links')

        return html

    def test_render_form_wrapper_class(self):
        html = self.render_form()

        self.assertIn('<div class="sequence-container sequence-type-list">', html)

    def test_render_form_count_field(self):
        html = self.render_form()

        self.assertIn('<input type="hidden" name="links-count" id="links-count" value="2">', html)

    def test_render_form_delete_field(self):
        html = self.render_form()

        self.assertIn('<input type="hidden" id="links-0-deleted" name="links-0-deleted" value="">', html)

    def test_render_form_order_fields(self):
        html = self.render_form()

        self.assertIn('<input type="hidden" id="links-0-order" name="links-0-order" value="0">', html)
        self.assertIn('<input type="hidden" id="links-1-order" name="links-1-order" value="1">', html)

    def test_render_form_labels(self):
        html = self.render_form()

        self.assertIn('<label for="links-0-value-title">Title:</label>', html)
        self.assertIn('<label for="links-0-value-link">Link:</label>', html)

    def test_render_form_values(self):
        html = self.render_form()

        self.assertInHTML(
            (
                '<input id="links-0-value-title" name="links-0-value-title" placeholder="Title"'
                ' type="text" value="Wagtail" />'
            ),
            html
        )
        self.assertInHTML(
            (
                '<input id="links-0-value-link" name="links-0-value-link" placeholder="Link" type="url"'
                ' value="http://www.wagtail.io" />'
            ),
            html
        )
        self.assertInHTML(
            (
                '<input id="links-1-value-title" name="links-1-value-title" placeholder="Title" type="text"'
                ' value="Django" />'
            ),
            html
        )
        self.assertInHTML(
            (
                '<input id="links-1-value-link" name="links-1-value-link" placeholder="Link"'
                ' type="url" value="http://www.djangoproject.com" />'
            ),
            html
        )

    def test_html_declarations(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            link = blocks.URLBlock()

        block = blocks.ListBlock(LinkBlock)
        html = block.html_declarations()

        self.assertTagInTemplateScript(
            '<input id="__PREFIX__-value-title" name="__PREFIX__-value-title" placeholder="Title" type="text" />',
            html
        )
        self.assertTagInTemplateScript(
            '<input id="__PREFIX__-value-link" name="__PREFIX__-value-link" placeholder="Link" type="url" />',
            html
        )

    def test_html_declarations_uses_default(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock(default="Github")
            link = blocks.URLBlock(default="http://www.github.com")

        block = blocks.ListBlock(LinkBlock)
        html = block.html_declarations()

        self.assertTagInTemplateScript(
            (
                '<input id="__PREFIX__-value-title" name="__PREFIX__-value-title" placeholder="Title"'
                ' type="text" value="Github" />'
            ),
            html
        )
        self.assertTagInTemplateScript(
            (
                '<input id="__PREFIX__-value-link" name="__PREFIX__-value-link" placeholder="Link"'
                ' type="url" value="http://www.github.com" />'
            ),
            html
        )

    def test_media_inheritance(self):
        class ScriptedCharBlock(blocks.CharBlock):
            media = forms.Media(js=['scripted_char_block.js'])

        block = blocks.ListBlock(ScriptedCharBlock())
        self.assertIn('scripted_char_block.js', ''.join(block.all_media().render_js()))

    def test_html_declaration_inheritance(self):
        class CharBlockWithDeclarations(blocks.CharBlock):
            def html_declarations(self):
                return '<script type="text/x-html-template">hello world</script>'

        block = blocks.ListBlock(CharBlockWithDeclarations())
        self.assertIn('<script type="text/x-html-template">hello world</script>', block.all_html_declarations())

    def test_searchable_content(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            link = blocks.URLBlock()

        block = blocks.ListBlock(LinkBlock())
        content = block.get_searchable_content([
            {
                'title': "Wagtail",
                'link': 'http://www.wagtail.io',
            },
            {
                'title': "Django",
                'link': 'http://www.djangoproject.com',
            },
        ])

        self.assertEqual(content, ["Wagtail", "Django"])

    def test_value_omitted_from_data(self):
        block = blocks.ListBlock(blocks.CharBlock())

        # overall value is considered present in the form if the 'count' field is present
        self.assertFalse(block.value_omitted_from_data({'mylist-count': '0'}, {}, 'mylist'))
        self.assertFalse(block.value_omitted_from_data({
            'mylist-count': '1',
            'mylist-0-value': 'hello', 'mylist-0-deleted': '', 'mylist-0-order': '0'
        }, {}, 'mylist'))
        self.assertTrue(block.value_omitted_from_data({'nothing-here': 'nope'}, {}, 'mylist'))

    def test_ordering_in_form_submission_uses_order_field(self):
        block = blocks.ListBlock(blocks.CharBlock())

        # check that items are ordered by the 'order' field, not the order they appear in the form
        post_data = {'shoppinglist-count': '3'}
        for i in range(0, 3):
            post_data.update({
                'shoppinglist-%d-deleted' % i: '',
                'shoppinglist-%d-order' % i: str(2 - i),
                'shoppinglist-%d-value' % i: "item %d" % i
            })

        block_value = block.value_from_datadict(post_data, {}, 'shoppinglist')
        self.assertEqual(block_value[2], "item 0")

    def test_ordering_in_form_submission_is_numeric(self):
        block = blocks.ListBlock(blocks.CharBlock())

        # check that items are ordered by 'order' numerically, not alphabetically
        post_data = {'shoppinglist-count': '12'}
        for i in range(0, 12):
            post_data.update({
                'shoppinglist-%d-deleted' % i: '',
                'shoppinglist-%d-order' % i: str(i),
                'shoppinglist-%d-value' % i: "item %d" % i
            })

        block_value = block.value_from_datadict(post_data, {}, 'shoppinglist')
        self.assertEqual(block_value[2], "item 2")

    def test_can_specify_default(self):
        class ShoppingListBlock(blocks.StructBlock):
            shop = blocks.CharBlock()
            items = blocks.ListBlock(blocks.CharBlock(), default=['peas', 'beans', 'carrots'])

        block = ShoppingListBlock()
        # the value here does not specify an 'items' field, so this should revert to the ListBlock's default
        form_html = block.render_form(block.to_python({'shop': 'Tesco'}), prefix='shoppinglist')

        self.assertIn(
            '<input type="hidden" name="shoppinglist-items-count" id="shoppinglist-items-count" value="3">',
            form_html
        )
        self.assertIn('value="peas"', form_html)

    def test_default_default(self):
        """
        if no explicit 'default' is set on the ListBlock, it should fall back on
        a single instance of the child block in its default state.
        """
        class ShoppingListBlock(blocks.StructBlock):
            shop = blocks.CharBlock()
            items = blocks.ListBlock(blocks.CharBlock(default='chocolate'))

        block = ShoppingListBlock()
        # the value here does not specify an 'items' field, so this should revert to the ListBlock's default
        form_html = block.render_form(block.to_python({'shop': 'Tesco'}), prefix='shoppinglist')

        self.assertIn(
            '<input type="hidden" name="shoppinglist-items-count" id="shoppinglist-items-count" value="1">',
            form_html
        )
        self.assertIn('value="chocolate"', form_html)


class TestStreamBlock(WagtailTestUtils, SimpleTestCase):
    def test_initialisation(self):
        block = blocks.StreamBlock([
            ('heading', blocks.CharBlock()),
            ('paragraph', blocks.CharBlock()),
        ])

        self.assertEqual(list(block.child_blocks.keys()), ['heading', 'paragraph'])

    def test_initialisation_with_binary_string_names(self):
        # migrations will sometimes write out names as binary strings, just to keep us on our toes
        block = blocks.StreamBlock([
            (b'heading', blocks.CharBlock()),
            (b'paragraph', blocks.CharBlock()),
        ])

        self.assertEqual(list(block.child_blocks.keys()), [b'heading', b'paragraph'])

    def test_initialisation_from_subclass(self):
        class ArticleBlock(blocks.StreamBlock):
            heading = blocks.CharBlock()
            paragraph = blocks.CharBlock()

        block = ArticleBlock()

        self.assertEqual(list(block.child_blocks.keys()), ['heading', 'paragraph'])

    def test_initialisation_from_subclass_with_extra(self):
        class ArticleBlock(blocks.StreamBlock):
            heading = blocks.CharBlock()
            paragraph = blocks.CharBlock()

        block = ArticleBlock([
            ('intro', blocks.CharBlock())
        ])

        self.assertEqual(list(block.child_blocks.keys()), ['heading', 'paragraph', 'intro'])

    def test_initialisation_with_multiple_subclassses(self):
        class ArticleBlock(blocks.StreamBlock):
            heading = blocks.CharBlock()
            paragraph = blocks.CharBlock()

        class ArticleWithIntroBlock(ArticleBlock):
            intro = blocks.CharBlock()

        block = ArticleWithIntroBlock()

        self.assertEqual(list(block.child_blocks.keys()), ['heading', 'paragraph', 'intro'])

    def test_initialisation_with_mixins(self):
        """
        The order of child blocks of ``StreamBlock``\s with multiple parent
        classes is slightly surprising at first. Child blocks are inherited in
        a bottom-up order, by traversing the MRO in reverse. In the example
        below, ``ArticleWithIntroBlock`` will have an MRO of::

            [ArticleWithIntroBlock, IntroMixin, ArticleBlock, StreamBlock, ...]

        This will result in ``intro`` appearing *after* ``heading`` and
        ``paragraph`` in ``ArticleWithIntroBlock.child_blocks``, even though
        ``IntroMixin`` appeared before ``ArticleBlock``.
        """
        class ArticleBlock(blocks.StreamBlock):
            heading = blocks.CharBlock()
            paragraph = blocks.CharBlock()

        class IntroMixin(blocks.StreamBlock):
            intro = blocks.CharBlock()

        class ArticleWithIntroBlock(IntroMixin, ArticleBlock):
            by_line = blocks.CharBlock()

        block = ArticleWithIntroBlock()

        self.assertEqual(list(block.child_blocks.keys()),
                         ['heading', 'paragraph', 'intro', 'by_line'])

    def test_required_raises_an_exception_if_empty(self):
        block = blocks.StreamBlock([('paragraph', blocks.CharBlock())], required=True)
        value = blocks.StreamValue(block, [])

        with self.assertRaises(blocks.StreamBlockValidationError):
            block.clean(value)

    def test_required_does_not_raise_an_exception_if_not_empty(self):
        block = blocks.StreamBlock([('paragraph', blocks.CharBlock())], required=True)
        value = block.to_python([{'type': 'paragraph', 'value': 'Hello'}])
        try:
            block.clean(value)
        except blocks.StreamBlockValidationError:
            raise self.failureException("%s was raised" % blocks.StreamBlockValidationError)

    def test_not_required_does_not_raise_an_exception_if_empty(self):
        block = blocks.StreamBlock([('paragraph', blocks.CharBlock())], required=False)
        value = blocks.StreamValue(block, [])

        try:
            block.clean(value)
        except blocks.StreamBlockValidationError:
            raise self.failureException("%s was raised" % blocks.StreamBlockValidationError)

    def test_required_by_default(self):
        block = blocks.StreamBlock([('paragraph', blocks.CharBlock())])
        value = blocks.StreamValue(block, [])

        with self.assertRaises(blocks.StreamBlockValidationError):
            block.clean(value)

    def render_article(self, data):
        class ArticleBlock(blocks.StreamBlock):
            heading = blocks.CharBlock()
            paragraph = blocks.RichTextBlock()

        block = ArticleBlock()
        value = block.to_python(data)

        return block.render(value)

    def test_get_api_representation_calls_same_method_on_children_with_context(self):
        """
        The get_api_representation method of a StreamBlock should invoke
        the block's get_api_representation method on each child and
        the context should be passed on.
        """
        class ContextBlock(blocks.CharBlock):
            def get_api_representation(self, value, context=None):
                return context[value]

        block = blocks.StreamBlock([
            ('language', ContextBlock()),
            ('author', ContextBlock()),
        ])
        api_representation = block.get_api_representation(
            block.to_python([
                {'type': 'language', 'value': 'en'},
                {'type': 'author', 'value': 'wagtail', 'id': '111111'},
            ]),
            context={
                'en': 'English',
                'wagtail': 'Wagtail!'
            }
        )

        self.assertListEqual(
            api_representation, [
                {'type': 'language', 'value': 'English', 'id': None},
                {'type': 'author', 'value': 'Wagtail!', 'id': '111111'},
            ]
        )

    def test_render(self):
        html = self.render_article([
            {
                'type': 'heading',
                'value': "My title",
            },
            {
                'type': 'paragraph',
                'value': 'My <i>first</i> paragraph',
            },
            {
                'type': 'paragraph',
                'value': 'My second paragraph',
            },
        ])

        self.assertIn('<div class="block-heading">My title</div>', html)
        self.assertIn('<div class="block-paragraph"><div class="rich-text">My <i>first</i> paragraph</div></div>', html)
        self.assertIn('<div class="block-paragraph"><div class="rich-text">My second paragraph</div></div>', html)

    def test_render_unknown_type(self):
        # This can happen if a developer removes a type from their StreamBlock
        html = self.render_article([
            {
                'type': 'foo',
                'value': "Hello",
            },
            {
                'type': 'paragraph',
                'value': 'My first paragraph',
            },
        ])
        self.assertNotIn('foo', html)
        self.assertNotIn('Hello', html)
        self.assertIn('<div class="block-paragraph"><div class="rich-text">My first paragraph</div></div>', html)

    def test_render_calls_block_render_on_children(self):
        """
        The default rendering of a StreamBlock should invoke the block's render method
        on each child, rather than just outputting the child value as a string.
        """
        block = blocks.StreamBlock([
            ('heading', blocks.CharBlock(template='tests/blocks/heading_block.html')),
            ('paragraph', blocks.CharBlock()),
        ])
        value = block.to_python([
            {'type': 'heading', 'value': 'Hello'}
        ])
        html = block.render(value)
        self.assertIn('<div class="block-heading"><h1>Hello</h1></div>', html)

        # calling render_as_block() on value (a StreamValue instance)
        # should be equivalent to block.render(value)
        html = value.render_as_block()
        self.assertIn('<div class="block-heading"><h1>Hello</h1></div>', html)

    def test_render_passes_context_to_children(self):
        block = blocks.StreamBlock([
            ('heading', blocks.CharBlock(template='tests/blocks/heading_block.html')),
            ('paragraph', blocks.CharBlock()),
        ])
        value = block.to_python([
            {'type': 'heading', 'value': 'Bonjour'}
        ])
        html = block.render(value, context={
            'language': 'fr',
        })
        self.assertIn('<div class="block-heading"><h1 lang="fr">Bonjour</h1></div>', html)

        # calling render_as_block(context=foo) on value (a StreamValue instance)
        # should be equivalent to block.render(value, context=foo)
        html = value.render_as_block(context={
            'language': 'fr',
        })
        self.assertIn('<div class="block-heading"><h1 lang="fr">Bonjour</h1></div>', html)

    def test_render_on_stream_child_uses_child_template(self):
        """
        Accessing a child element of the stream (giving a StreamChild object) and rendering it
        should use the block template, not just render the value's string representation
        """
        block = blocks.StreamBlock([
            ('heading', blocks.CharBlock(template='tests/blocks/heading_block.html')),
            ('paragraph', blocks.CharBlock()),
        ])
        value = block.to_python([
            {'type': 'heading', 'value': 'Hello'}
        ])
        html = value[0].render()
        self.assertEqual('<h1>Hello</h1>', html)

        # StreamChild.__str__ should do the same
        html = str(value[0])
        self.assertEqual('<h1>Hello</h1>', html)

        # and so should StreamChild.render_as_block
        html = value[0].render_as_block()
        self.assertEqual('<h1>Hello</h1>', html)

    def test_can_pass_context_to_stream_child_template(self):
        block = blocks.StreamBlock([
            ('heading', blocks.CharBlock(template='tests/blocks/heading_block.html')),
            ('paragraph', blocks.CharBlock()),
        ])
        value = block.to_python([
            {'type': 'heading', 'value': 'Bonjour'}
        ])
        html = value[0].render(context={'language': 'fr'})
        self.assertEqual('<h1 lang="fr">Bonjour</h1>', html)

        # the same functionality should be available through the alias `render_as_block`
        html = value[0].render_as_block(context={'language': 'fr'})
        self.assertEqual('<h1 lang="fr">Bonjour</h1>', html)

    def render_form(self):
        class ArticleBlock(blocks.StreamBlock):
            heading = blocks.CharBlock()
            paragraph = blocks.CharBlock()

        block = ArticleBlock()
        value = block.to_python([
            {
                'type': 'heading',
                'value': "My title",
                'id': '123123123',
            },
            {
                'type': 'paragraph',
                'value': 'My first paragraph',
            },
            {
                'type': 'paragraph',
                'value': 'My second paragraph',
            },
        ])
        return block.render_form(value, prefix='myarticle')

    def test_render_form_wrapper_class(self):
        html = self.render_form()

        self.assertIn('<div class="sequence-container sequence-type-stream">', html)

    def test_render_form_count_field(self):
        html = self.render_form()

        self.assertIn('<input type="hidden" name="myarticle-count" id="myarticle-count" value="3">', html)

    def test_render_form_delete_field(self):
        html = self.render_form()

        self.assertIn('<input type="hidden" id="myarticle-0-deleted" name="myarticle-0-deleted" value="">', html)

    def test_render_form_order_fields(self):
        html = self.render_form()

        self.assertIn('<input type="hidden" id="myarticle-0-order" name="myarticle-0-order" value="0">', html)
        self.assertIn('<input type="hidden" id="myarticle-1-order" name="myarticle-1-order" value="1">', html)
        self.assertIn('<input type="hidden" id="myarticle-2-order" name="myarticle-2-order" value="2">', html)

    def test_render_form_id_fields(self):
        html = self.render_form()

        self.assertIn('<input type="hidden" id="myarticle-0-id" name="myarticle-0-id" value="123123123">', html)
        self.assertIn('<input type="hidden" id="myarticle-1-id" name="myarticle-1-id" value="">', html)
        self.assertIn('<input type="hidden" id="myarticle-2-id" name="myarticle-2-id" value="">', html)

    def test_render_form_type_fields(self):
        html = self.render_form()

        self.assertIn('<input type="hidden" id="myarticle-0-type" name="myarticle-0-type" value="heading">', html)
        self.assertIn('<input type="hidden" id="myarticle-1-type" name="myarticle-1-type" value="paragraph">', html)
        self.assertIn('<input type="hidden" id="myarticle-2-type" name="myarticle-2-type" value="paragraph">', html)

    def test_render_form_value_fields(self):
        html = self.render_form()

        self.assertInHTML(
            (
                '<input id="myarticle-0-value" name="myarticle-0-value" placeholder="Heading"'
                ' type="text" value="My title" />'
            ),
            html
        )
        self.assertInHTML(
            (
                '<input id="myarticle-1-value" name="myarticle-1-value" placeholder="Paragraph"'
                ' type="text" value="My first paragraph" />'
            ),
            html
        )
        self.assertInHTML(
            (
                '<input id="myarticle-2-value" name="myarticle-2-value" placeholder="Paragraph"'
                ' type="text" value="My second paragraph" />'
            ),
            html
        )

    def test_value_omitted_from_data(self):
        block = blocks.StreamBlock([
            ('heading', blocks.CharBlock()),
        ])

        # overall value is considered present in the form if the 'count' field is present
        self.assertFalse(block.value_omitted_from_data({'mystream-count': '0'}, {}, 'mystream'))
        self.assertFalse(block.value_omitted_from_data({
            'mystream-count': '1',
            'mystream-0-type': 'heading', 'mystream-0-value': 'hello',
            'mystream-0-deleted': '', 'mystream-0-order': '0'
        }, {}, 'mystream'))
        self.assertTrue(block.value_omitted_from_data({'nothing-here': 'nope'}, {}, 'mystream'))

    def test_validation_errors(self):
        class ValidatedBlock(blocks.StreamBlock):
            char = blocks.CharBlock()
            url = blocks.URLBlock()
        block = ValidatedBlock()

        value = blocks.StreamValue(block, [
            ('char', ''),
            ('char', 'foo'),
            ('url', 'http://example.com/'),
            ('url', 'not a url'),
        ])

        with self.assertRaises(ValidationError) as catcher:
            block.clean(value)
        self.assertEqual(catcher.exception.params, {
            0: ['This field is required.'],
            3: ['Enter a valid URL.'],
        })

    def test_min_num_validation_errors(self):
        class ValidatedBlock(blocks.StreamBlock):
            char = blocks.CharBlock()
            url = blocks.URLBlock()
        block = ValidatedBlock(min_num=1)

        value = blocks.StreamValue(block, [])

        with self.assertRaises(ValidationError) as catcher:
            block.clean(value)
        self.assertEqual(catcher.exception.params, {
            '__all__': ['The minimum number of items is 1']
        })

        # a value with >= 1 blocks should pass validation
        value = blocks.StreamValue(block, [('char', 'foo')])
        self.assertTrue(block.clean(value))

    def test_max_num_validation_errors(self):
        class ValidatedBlock(blocks.StreamBlock):
            char = blocks.CharBlock()
            url = blocks.URLBlock()
        block = ValidatedBlock(max_num=1)

        value = blocks.StreamValue(block, [
            ('char', 'foo'),
            ('char', 'foo'),
            ('url', 'http://example.com/'),
            ('url', 'http://example.com/'),
        ])

        with self.assertRaises(ValidationError) as catcher:
            block.clean(value)
        self.assertEqual(catcher.exception.params, {
            '__all__': ['The maximum number of items is 1']
        })

        # a value with 1 block should pass validation
        value = blocks.StreamValue(block, [('char', 'foo')])
        self.assertTrue(block.clean(value))

    def test_block_counts_min_validation_errors(self):
        class ValidatedBlock(blocks.StreamBlock):
            char = blocks.CharBlock()
            url = blocks.URLBlock()
        block = ValidatedBlock(block_counts={'char': {'min_num': 1}})

        value = blocks.StreamValue(block, [
            ('url', 'http://example.com/'),
            ('url', 'http://example.com/'),
        ])

        with self.assertRaises(ValidationError) as catcher:
            block.clean(value)
        self.assertEqual(catcher.exception.params, {
            '__all__': ['Char: The minimum number of items is 1']
        })

        # a value with 1 char block should pass validation
        value = blocks.StreamValue(block, [
            ('url', 'http://example.com/'),
            ('char', 'foo'),
            ('url', 'http://example.com/'),
        ])
        self.assertTrue(block.clean(value))

    def test_block_counts_max_validation_errors(self):
        class ValidatedBlock(blocks.StreamBlock):
            char = blocks.CharBlock()
            url = blocks.URLBlock()
        block = ValidatedBlock(block_counts={'char': {'max_num': 1}})

        value = blocks.StreamValue(block, [
            ('char', 'foo'),
            ('char', 'foo'),
            ('url', 'http://example.com/'),
            ('url', 'http://example.com/'),
        ])

        with self.assertRaises(ValidationError) as catcher:
            block.clean(value)
        self.assertEqual(catcher.exception.params, {
            '__all__': ['Char: The maximum number of items is 1']
        })

        # a value with 1 char block should pass validation
        value = blocks.StreamValue(block, [
            ('char', 'foo'),
            ('url', 'http://example.com/'),
            ('url', 'http://example.com/'),
        ])
        self.assertTrue(block.clean(value))

    def test_block_level_validation_renders_errors(self):
        block = FooStreamBlock()

        post_data = {'stream-count': '2'}
        for i, value in enumerate(['bar', 'baz']):
            post_data.update({
                'stream-%d-deleted' % i: '',
                'stream-%d-order' % i: str(i),
                'stream-%d-type' % i: 'text',
                'stream-%d-value' % i: value,
            })

        block_value = block.value_from_datadict(post_data, {}, 'stream')
        with self.assertRaises(ValidationError) as catcher:
            block.clean(block_value)

        errors = ErrorList([
            catcher.exception
        ])

        self.assertInHTML(
            format_html('<div class="help-block help-critical">{}</div>', FooStreamBlock.error),
            block.render_form(block_value, prefix='stream', errors=errors))

    def test_block_level_validation_render_no_errors(self):
        block = FooStreamBlock()

        post_data = {'stream-count': '3'}
        for i, value in enumerate(['foo', 'bar', 'baz']):
            post_data.update({
                'stream-%d-deleted' % i: '',
                'stream-%d-order' % i: str(i),
                'stream-%d-type' % i: 'text',
                'stream-%d-value' % i: value,
            })

        block_value = block.value_from_datadict(post_data, {}, 'stream')

        try:
            block.clean(block_value)
        except ValidationError:
            self.fail('Should have passed validation')

        self.assertInHTML(
            format_html('<div class="help-block help-critical">{}</div>', FooStreamBlock.error),
            block.render_form(block_value, prefix='stream'),
            count=0)

    def test_html_declarations(self):
        class ArticleBlock(blocks.StreamBlock):
            heading = blocks.CharBlock()
            paragraph = blocks.CharBlock()

        block = ArticleBlock()
        html = block.html_declarations()

        self.assertTagInTemplateScript('<input type="hidden" id="__PREFIX__-id" name="__PREFIX__-id" value="" />', html)
        self.assertTagInTemplateScript('<input type="hidden" id="__PREFIX__-type" name="__PREFIX__-type" value="heading" />', html)
        self.assertTagInTemplateScript('<input id="__PREFIX__-value" name="__PREFIX__-value" placeholder="Heading" type="text" />', html)
        self.assertTagInTemplateScript(
            '<input id="__PREFIX__-value" name="__PREFIX__-value" placeholder="Paragraph" type="text" />',
            html
        )

    def test_html_declarations_uses_default(self):
        class ArticleBlock(blocks.StreamBlock):
            heading = blocks.CharBlock(default="Fish found on moon")
            paragraph = blocks.CharBlock(default="Lorem ipsum dolor sit amet")

        block = ArticleBlock()
        html = block.html_declarations()

        self.assertTagInTemplateScript(
            (
                '<input id="__PREFIX__-value" name="__PREFIX__-value" placeholder="Heading"'
                ' type="text" value="Fish found on moon" />'
            ),
            html
        )
        self.assertTagInTemplateScript(
            (
                '<input id="__PREFIX__-value" name="__PREFIX__-value" placeholder="Paragraph" type="text"'
                ' value="Lorem ipsum dolor sit amet" />'
            ),
            html
        )

    def test_media_inheritance(self):
        class ScriptedCharBlock(blocks.CharBlock):
            media = forms.Media(js=['scripted_char_block.js'])

        class ArticleBlock(blocks.StreamBlock):
            heading = ScriptedCharBlock()
            paragraph = blocks.CharBlock()

        block = ArticleBlock()
        self.assertIn('scripted_char_block.js', ''.join(block.all_media().render_js()))

    def test_html_declaration_inheritance(self):
        class CharBlockWithDeclarations(blocks.CharBlock):
            def html_declarations(self):
                return '<script type="text/x-html-template">hello world</script>'

        class ArticleBlock(blocks.StreamBlock):
            heading = CharBlockWithDeclarations(default="Torchbox")
            paragraph = blocks.CharBlock()

        block = ArticleBlock()
        self.assertIn('<script type="text/x-html-template">hello world</script>', block.all_html_declarations())

    def test_ordering_in_form_submission_uses_order_field(self):
        class ArticleBlock(blocks.StreamBlock):
            heading = blocks.CharBlock()
            paragraph = blocks.CharBlock()

        block = ArticleBlock()

        # check that items are ordered by the 'order' field, not the order they appear in the form
        post_data = {'article-count': '3'}
        for i in range(0, 3):
            post_data.update({
                'article-%d-deleted' % i: '',
                'article-%d-order' % i: str(2 - i),
                'article-%d-type' % i: 'heading',
                'article-%d-value' % i: "heading %d" % i,
                'article-%d-id' % i: "000%d" % i,
            })

        block_value = block.value_from_datadict(post_data, {}, 'article')
        self.assertEqual(block_value[2].value, "heading 0")
        self.assertEqual(block_value[2].id, "0000")

    def test_ordering_in_form_submission_is_numeric(self):
        class ArticleBlock(blocks.StreamBlock):
            heading = blocks.CharBlock()
            paragraph = blocks.CharBlock()

        block = ArticleBlock()

        # check that items are ordered by 'order' numerically, not alphabetically
        post_data = {'article-count': '12'}
        for i in range(0, 12):
            post_data.update({
                'article-%d-deleted' % i: '',
                'article-%d-order' % i: str(i),
                'article-%d-type' % i: 'heading',
                'article-%d-value' % i: "heading %d" % i
            })

        block_value = block.value_from_datadict(post_data, {}, 'article')
        self.assertEqual(block_value[2].value, "heading 2")

    def test_searchable_content(self):
        class ArticleBlock(blocks.StreamBlock):
            heading = blocks.CharBlock()
            paragraph = blocks.CharBlock()

        block = ArticleBlock()
        value = block.to_python([
            {
                'type': 'heading',
                'value': "My title",
            },
            {
                'type': 'paragraph',
                'value': 'My first paragraph',
            },
            {
                'type': 'paragraph',
                'value': 'My second paragraph',
            },
        ])

        content = block.get_searchable_content(value)

        self.assertEqual(content, [
            "My title",
            "My first paragraph",
            "My second paragraph",
        ])

    def test_meta_default(self):
        """Test that we can specify a default value in the Meta of a StreamBlock"""

        class ArticleBlock(blocks.StreamBlock):
            heading = blocks.CharBlock()
            paragraph = blocks.CharBlock()

            class Meta:
                default = [('heading', 'A default heading')]

        # to access the default value, we retrieve it through a StructBlock
        # from a struct value that's missing that key
        class ArticleContainerBlock(blocks.StructBlock):
            author = blocks.CharBlock()
            article = ArticleBlock()

        block = ArticleContainerBlock()
        struct_value = block.to_python({'author': 'Bob'})
        stream_value = struct_value['article']

        self.assertTrue(isinstance(stream_value, blocks.StreamValue))
        self.assertEqual(len(stream_value), 1)
        self.assertEqual(stream_value[0].block_type, 'heading')
        self.assertEqual(stream_value[0].value, 'A default heading')

    def test_constructor_default(self):
        """Test that we can specify a default value in the constructor of a StreamBlock"""

        class ArticleBlock(blocks.StreamBlock):
            heading = blocks.CharBlock()
            paragraph = blocks.CharBlock()

            class Meta:
                default = [('heading', 'A default heading')]

        # to access the default value, we retrieve it through a StructBlock
        # from a struct value that's missing that key
        class ArticleContainerBlock(blocks.StructBlock):
            author = blocks.CharBlock()
            article = ArticleBlock(default=[('heading', 'A different default heading')])

        block = ArticleContainerBlock()
        struct_value = block.to_python({'author': 'Bob'})
        stream_value = struct_value['article']

        self.assertTrue(isinstance(stream_value, blocks.StreamValue))
        self.assertEqual(len(stream_value), 1)
        self.assertEqual(stream_value[0].block_type, 'heading')
        self.assertEqual(stream_value[0].value, 'A different default heading')

    def test_stream_value_equality(self):
        block = blocks.StreamBlock([
            ('text', blocks.CharBlock()),
        ])
        value1 = block.to_python([{'type': 'text', 'value': 'hello'}])
        value2 = block.to_python([{'type': 'text', 'value': 'hello'}])
        value3 = block.to_python([{'type': 'text', 'value': 'goodbye'}])

        self.assertTrue(value1 == value2)
        self.assertFalse(value1 != value2)

        self.assertFalse(value1 == value3)
        self.assertTrue(value1 != value3)

    def test_render_considers_group_attribute(self):
        """If group attributes are set in Block Meta classes, render a <h3> for each different block"""

        class Group1Block1(blocks.CharBlock):
            class Meta:
                group = 'group1'

        class Group1Block2(blocks.CharBlock):
            class Meta:
                group = 'group1'

        class Group2Block1(blocks.CharBlock):
            class Meta:
                group = 'group2'

        class Group2Block2(blocks.CharBlock):
            class Meta:
                group = 'group2'

        class NoGroupBlock(blocks.CharBlock):
            pass

        block = blocks.StreamBlock([
            ('b1', Group1Block1()),
            ('b2', Group1Block2()),
            ('b3', Group2Block1()),
            ('b4', Group2Block2()),
            ('ngb', NoGroupBlock()),
        ])
        html = block.render_form('')
        self.assertNotIn('<h3></h3>', block.render_form(''))
        self.assertIn('<h3>group1</h3>', html)
        self.assertIn('<h3>group2</h3>', html)

    def test_value_from_datadict(self):
        class ArticleBlock(blocks.StreamBlock):
            heading = blocks.CharBlock()
            paragraph = blocks.CharBlock()

        block = ArticleBlock()

        value = block.value_from_datadict({
            'foo-count': '3',
            'foo-0-deleted': '',
            'foo-0-order': '2',
            'foo-0-type': 'heading',
            'foo-0-id': '0000',
            'foo-0-value': 'this is my heading',
            'foo-1-deleted': '1',
            'foo-1-order': '1',
            'foo-1-type': 'heading',
            'foo-1-id': '0001',
            'foo-1-value': 'a deleted heading',
            'foo-2-deleted': '',
            'foo-2-order': '0',
            'foo-2-type': 'paragraph',
            'foo-2-id': '',
            'foo-2-value': '<p>this is a paragraph</p>',
        }, {}, prefix='foo')

        self.assertEqual(len(value), 2)
        self.assertEqual(value[0].block_type, 'paragraph')
        self.assertEqual(value[0].id, '')
        self.assertEqual(value[0].value, '<p>this is a paragraph</p>')

        self.assertEqual(value[1].block_type, 'heading')
        self.assertEqual(value[1].id, '0000')
        self.assertEqual(value[1].value, 'this is my heading')

    def test_get_prep_value(self):
        class ArticleBlock(blocks.StreamBlock):
            heading = blocks.CharBlock()
            paragraph = blocks.CharBlock()

        block = ArticleBlock()

        value = blocks.StreamValue(block, [
            ('heading', 'this is my heading', '0000'),
            ('paragraph', '<p>this is a paragraph</p>')
        ])
        jsonish_value = block.get_prep_value(value)

        self.assertEqual(len(jsonish_value), 2)
        self.assertEqual(jsonish_value[0], {'type': 'heading', 'value': 'this is my heading', 'id': '0000'})
        self.assertEqual(jsonish_value[1]['type'], 'paragraph')
        self.assertEqual(jsonish_value[1]['value'], '<p>this is a paragraph</p>')
        # get_prep_value should assign a new (random and non-empty) ID to this block, as it didn't
        # have one already
        self.assertTrue(jsonish_value[1]['id'])


class TestPageChooserBlock(TestCase):
    fixtures = ['test.json']

    def test_serialize(self):
        """The value of a PageChooserBlock (a Page object) should serialize to an ID"""
        block = blocks.PageChooserBlock()
        christmas_page = Page.objects.get(slug='christmas')

        self.assertEqual(block.get_prep_value(christmas_page), christmas_page.id)

        # None should serialize to None
        self.assertEqual(block.get_prep_value(None), None)

    def test_deserialize(self):
        """The serialized value of a PageChooserBlock (an ID) should deserialize to a Page object"""
        block = blocks.PageChooserBlock()
        christmas_page = Page.objects.get(slug='christmas')

        self.assertEqual(block.to_python(christmas_page.id), christmas_page)

        # None should deserialize to None
        self.assertEqual(block.to_python(None), None)

    def test_form_render(self):
        block = blocks.PageChooserBlock(help_text="pick a page, any page")

        empty_form_html = block.render_form(None, 'page')
        self.assertInHTML('<input id="page" name="page" placeholder="" type="hidden" />', empty_form_html)
        self.assertIn('createPageChooser("page", ["wagtailcore.page"], null, false, null);', empty_form_html)

        christmas_page = Page.objects.get(slug='christmas')
        christmas_form_html = block.render_form(christmas_page, 'page')
        expected_html = '<input id="page" name="page" placeholder="" type="hidden" value="%d" />' % christmas_page.id
        self.assertInHTML(expected_html, christmas_form_html)
        self.assertIn("pick a page, any page", christmas_form_html)

    def test_form_render_with_target_model_default(self):
        block = blocks.PageChooserBlock()
        empty_form_html = block.render_form(None, 'page')
        self.assertIn('createPageChooser("page", ["wagtailcore.page"], null, false, null);', empty_form_html)

    def test_form_render_with_target_model_string(self):
        block = blocks.PageChooserBlock(help_text="pick a page, any page", target_model='tests.SimplePage')
        empty_form_html = block.render_form(None, 'page')
        self.assertIn('createPageChooser("page", ["tests.simplepage"], null, false, null);', empty_form_html)

    def test_form_render_with_target_model_literal(self):
        block = blocks.PageChooserBlock(help_text="pick a page, any page", target_model=SimplePage)
        empty_form_html = block.render_form(None, 'page')
        self.assertIn('createPageChooser("page", ["tests.simplepage"], null, false, null);', empty_form_html)

    def test_form_render_with_target_model_multiple_strings(self):
        block = blocks.PageChooserBlock(help_text="pick a page, any page", target_model=['tests.SimplePage', 'tests.EventPage'])
        empty_form_html = block.render_form(None, 'page')
        self.assertIn('createPageChooser("page", ["tests.simplepage", "tests.eventpage"], null, false, null);', empty_form_html)

    def test_form_render_with_target_model_multiple_literals(self):
        block = blocks.PageChooserBlock(help_text="pick a page, any page", target_model=[SimplePage, EventPage])
        empty_form_html = block.render_form(None, 'page')
        self.assertIn('createPageChooser("page", ["tests.simplepage", "tests.eventpage"], null, false, null);', empty_form_html)

    def test_form_render_with_can_choose_root(self):
        block = blocks.PageChooserBlock(help_text="pick a page, any page", can_choose_root=True)
        empty_form_html = block.render_form(None, 'page')
        self.assertIn('createPageChooser("page", ["wagtailcore.page"], null, true, null);', empty_form_html)

    def test_form_response(self):
        block = blocks.PageChooserBlock()
        christmas_page = Page.objects.get(slug='christmas')

        value = block.value_from_datadict({'page': str(christmas_page.id)}, {}, 'page')
        self.assertEqual(value, christmas_page)

        empty_value = block.value_from_datadict({'page': ''}, {}, 'page')
        self.assertEqual(empty_value, None)

    def test_clean(self):
        required_block = blocks.PageChooserBlock()
        nonrequired_block = blocks.PageChooserBlock(required=False)
        christmas_page = Page.objects.get(slug='christmas')

        self.assertEqual(required_block.clean(christmas_page), christmas_page)
        with self.assertRaises(ValidationError):
            required_block.clean(None)

        self.assertEqual(nonrequired_block.clean(christmas_page), christmas_page)
        self.assertEqual(nonrequired_block.clean(None), None)

    def test_target_model_default(self):
        block = blocks.PageChooserBlock()
        self.assertEqual(block.target_model, Page)

    def test_target_model_string(self):
        block = blocks.PageChooserBlock(target_model='tests.SimplePage')
        self.assertEqual(block.target_model, SimplePage)

    def test_target_model_literal(self):
        block = blocks.PageChooserBlock(target_model=SimplePage)
        self.assertEqual(block.target_model, SimplePage)

    def test_target_model_multiple_strings(self):
        block = blocks.PageChooserBlock(target_model=['tests.SimplePage', 'tests.EventPage'])
        self.assertEqual(block.target_model, Page)

    def test_target_model_multiple_literals(self):
        block = blocks.PageChooserBlock(target_model=[SimplePage, EventPage])
        self.assertEqual(block.target_model, Page)

    def test_deconstruct_target_model_default(self):
        block = blocks.PageChooserBlock()
        self.assertEqual(block.deconstruct(), (
            'wagtail.core.blocks.PageChooserBlock',
            (), {}))

    def test_deconstruct_target_model_string(self):
        block = blocks.PageChooserBlock(target_model='tests.SimplePage')
        self.assertEqual(block.deconstruct(), (
            'wagtail.core.blocks.PageChooserBlock',
            (), {'target_model': ['tests.SimplePage']}))

    def test_deconstruct_target_model_literal(self):
        block = blocks.PageChooserBlock(target_model=SimplePage)
        self.assertEqual(block.deconstruct(), (
            'wagtail.core.blocks.PageChooserBlock',
            (), {'target_model': ['tests.SimplePage']}))

    def test_deconstruct_target_model_multiple_strings(self):
        block = blocks.PageChooserBlock(target_model=['tests.SimplePage', 'tests.EventPage'])
        self.assertEqual(block.deconstruct(), (
            'wagtail.core.blocks.PageChooserBlock',
            (), {'target_model': ['tests.SimplePage', 'tests.EventPage']}))

    def test_deconstruct_target_model_multiple_literals(self):
        block = blocks.PageChooserBlock(target_model=[SimplePage, EventPage])
        self.assertEqual(block.deconstruct(), (
            'wagtail.core.blocks.PageChooserBlock',
            (), {'target_model': ['tests.SimplePage', 'tests.EventPage']}))


class TestStaticBlock(unittest.TestCase):
    def test_render_form_with_constructor(self):
        block = blocks.StaticBlock(
            admin_text="Latest posts - This block doesn't need to be configured, it will be displayed automatically",
            template='tests/blocks/posts_static_block.html')
        rendered_html = block.render_form(None)

        self.assertEqual(rendered_html, "Latest posts - This block doesn't need to be configured, it will be displayed automatically")

    def test_render_form_with_subclass(self):
        class PostsStaticBlock(blocks.StaticBlock):
            class Meta:
                admin_text = "Latest posts - This block doesn't need to be configured, it will be displayed automatically"
                template = "tests/blocks/posts_static_block.html"

        block = PostsStaticBlock()
        rendered_html = block.render_form(None)

        self.assertEqual(rendered_html, "Latest posts - This block doesn't need to be configured, it will be displayed automatically")

    def test_render_form_with_subclass_displays_default_text_if_no_admin_text(self):
        class LabelOnlyStaticBlock(blocks.StaticBlock):
            class Meta:
                label = "Latest posts"

        block = LabelOnlyStaticBlock()
        rendered_html = block.render_form(None)

        self.assertEqual(rendered_html, "Latest posts: this block has no options.")

    def test_render_form_with_subclass_displays_default_text_if_no_admin_text_and_no_label(self):
        class NoMetaStaticBlock(blocks.StaticBlock):
            pass

        block = NoMetaStaticBlock()
        rendered_html = block.render_form(None)

        self.assertEqual(rendered_html, "This block has no options.")

    def test_render_form_works_with_mark_safe(self):
        block = blocks.StaticBlock(
            admin_text=mark_safe("<b>Latest posts</b> - This block doesn't need to be configured, it will be displayed automatically"),
            template='tests/blocks/posts_static_block.html')
        rendered_html = block.render_form(None)

        self.assertEqual(rendered_html, "<b>Latest posts</b> - This block doesn't need to be configured, it will be displayed automatically")

    def test_get_default(self):
        block = blocks.StaticBlock()
        default_value = block.get_default()
        self.assertEqual(default_value, None)

    def test_render(self):
        block = blocks.StaticBlock(template='tests/blocks/posts_static_block.html')
        result = block.render(None)
        self.assertEqual(result, '<p>PostsStaticBlock template</p>')

    def test_serialize(self):
        block = blocks.StaticBlock()
        result = block.get_prep_value(None)
        self.assertEqual(result, None)

    def test_deserialize(self):
        block = blocks.StaticBlock()
        result = block.to_python(None)
        self.assertEqual(result, None)


class TestDateBlock(TestCase):

    def test_render_form(self):
        block = blocks.DateBlock()
        value = date(2015, 8, 13)
        result = block.render_form(value, prefix='dateblock')

        # we should see the JS initialiser code:
        # <script>initDateChooser("dateblock", {"dayOfWeekStart": 0, "format": "Y-m-d"});</script>
        # except that we can't predict the order of the config options
        self.assertIn('<script>initDateChooser("dateblock", {', result)
        self.assertIn('"dayOfWeekStart": 0', result)
        self.assertIn('"format": "Y-m-d"', result)

        self.assertInHTML(
            '<input id="dateblock" name="dateblock" placeholder="" type="text" value="2015-08-13" />',
            result
        )

    def test_render_form_with_format(self):
        block = blocks.DateBlock(format='%d.%m.%Y')
        value = date(2015, 8, 13)
        result = block.render_form(value, prefix='dateblock')

        self.assertIn('<script>initDateChooser("dateblock", {', result)
        self.assertIn('"dayOfWeekStart": 0', result)
        self.assertIn('"format": "d.m.Y"', result)
        self.assertInHTML(
            '<input id="dateblock" name="dateblock" placeholder="" type="text" value="13.08.2015" />',
            result
        )


class TestDateTimeBlock(TestCase):

    def test_render_form_with_format(self):
        block = blocks.DateTimeBlock(format='%d.%m.%Y %H:%M')
        value = datetime(2015, 8, 13, 10, 0)
        result = block.render_form(value, prefix='datetimeblock')
        self.assertIn(
            '"format": "d.m.Y H:i"',
            result
        )
        self.assertInHTML(
            '<input id="datetimeblock" name="datetimeblock" placeholder="" type="text" value="13.08.2015 10:00" />',
            result
        )


class TestSystemCheck(TestCase):
    def test_name_must_be_nonempty(self):
        block = blocks.StreamBlock([
            ('heading', blocks.CharBlock()),
            ('', blocks.RichTextBlock()),
        ])

        errors = block.check()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].id, 'wagtailcore.E001')
        self.assertEqual(errors[0].hint, "Block name cannot be empty")
        self.assertEqual(errors[0].obj, block.child_blocks[''])

    def test_name_cannot_contain_spaces(self):
        block = blocks.StreamBlock([
            ('heading', blocks.CharBlock()),
            ('rich text', blocks.RichTextBlock()),
        ])

        errors = block.check()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].id, 'wagtailcore.E001')
        self.assertEqual(errors[0].hint, "Block names cannot contain spaces")
        self.assertEqual(errors[0].obj, block.child_blocks['rich text'])

    def test_name_cannot_contain_dashes(self):
        block = blocks.StreamBlock([
            ('heading', blocks.CharBlock()),
            ('rich-text', blocks.RichTextBlock()),
        ])

        errors = block.check()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].id, 'wagtailcore.E001')
        self.assertEqual(errors[0].hint, "Block names cannot contain dashes")
        self.assertEqual(errors[0].obj, block.child_blocks['rich-text'])

    def test_name_cannot_begin_with_digit(self):
        block = blocks.StreamBlock([
            ('heading', blocks.CharBlock()),
            ('99richtext', blocks.RichTextBlock()),
        ])

        errors = block.check()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].id, 'wagtailcore.E001')
        self.assertEqual(errors[0].hint, "Block names cannot begin with a digit")
        self.assertEqual(errors[0].obj, block.child_blocks['99richtext'])

    def test_system_checks_recurse_into_lists(self):
        failing_block = blocks.RichTextBlock()
        block = blocks.StreamBlock([
            ('paragraph_list', blocks.ListBlock(
                blocks.StructBlock([
                    ('heading', blocks.CharBlock()),
                    ('rich text', failing_block),
                ])
            ))
        ])

        errors = block.check()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].id, 'wagtailcore.E001')
        self.assertEqual(errors[0].hint, "Block names cannot contain spaces")
        self.assertEqual(errors[0].obj, failing_block)

    def test_system_checks_recurse_into_streams(self):
        failing_block = blocks.RichTextBlock()
        block = blocks.StreamBlock([
            ('carousel', blocks.StreamBlock([
                ('text', blocks.StructBlock([
                    ('heading', blocks.CharBlock()),
                    ('rich text', failing_block),
                ]))
            ]))
        ])

        errors = block.check()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].id, 'wagtailcore.E001')
        self.assertEqual(errors[0].hint, "Block names cannot contain spaces")
        self.assertEqual(errors[0].obj, failing_block)

    def test_system_checks_recurse_into_structs(self):
        failing_block_1 = blocks.RichTextBlock()
        failing_block_2 = blocks.RichTextBlock()
        block = blocks.StreamBlock([
            ('two_column', blocks.StructBlock([
                ('left', blocks.StructBlock([
                    ('heading', blocks.CharBlock()),
                    ('rich text', failing_block_1),
                ])),
                ('right', blocks.StructBlock([
                    ('heading', blocks.CharBlock()),
                    ('rich text', failing_block_2),
                ]))
            ]))
        ])

        errors = block.check()
        self.assertEqual(len(errors), 2)
        self.assertEqual(errors[0].id, 'wagtailcore.E001')
        self.assertEqual(errors[0].hint, "Block names cannot contain spaces")
        self.assertEqual(errors[0].obj, failing_block_1)
        self.assertEqual(errors[1].id, 'wagtailcore.E001')
        self.assertEqual(errors[1].hint, "Block names cannot contain spaces")
        self.assertEqual(errors[1].obj, failing_block_2)


class TestTemplateRendering(TestCase):
    def test_render_with_custom_context(self):
        block = CustomLinkBlock()
        value = block.to_python({'title': 'Torchbox', 'url': 'http://torchbox.com/'})
        context = {'classname': 'important'}
        result = block.render(value, context)

        self.assertEqual(result, '<a href="http://torchbox.com/" class="important">Torchbox</a>')

    def test_render_with_custom_form_context(self):
        block = CustomLinkBlock()
        value = block.to_python({'title': 'Torchbox', 'url': 'http://torchbox.com/'})
        result = block.render_form(value, prefix='my-link-block')

        self.assertIn('data-prefix="my-link-block"', result)
        self.assertIn('<p>Hello from get_form_context!</p>', result)


class TestIncludeBlockTag(TestCase):
    def test_include_block_tag_with_boundblock(self):
        """
        The include_block tag should be able to render a BoundBlock's template
        while keeping the parent template's context
        """
        block = blocks.CharBlock(template='tests/blocks/heading_block.html')
        bound_block = block.bind('bonjour')

        result = render_to_string('tests/blocks/include_block_test.html', {
            'test_block': bound_block,
            'language': 'fr',
        })
        self.assertIn('<body><h1 lang="fr">bonjour</h1></body>', result)

    def test_include_block_tag_with_structvalue(self):
        """
        The include_block tag should be able to render a StructValue's template
        while keeping the parent template's context
        """
        block = SectionBlock()
        struct_value = block.to_python({'title': 'Bonjour', 'body': 'monde <i>italique</i>'})

        result = render_to_string('tests/blocks/include_block_test.html', {
            'test_block': struct_value,
            'language': 'fr',
        })

        self.assertIn(
            """<body><h1 lang="fr">Bonjour</h1><div class="rich-text">monde <i>italique</i></div></body>""",
            result
        )

    def test_include_block_tag_with_streamvalue(self):
        """
        The include_block tag should be able to render a StreamValue's template
        while keeping the parent template's context
        """
        block = blocks.StreamBlock([
            ('heading', blocks.CharBlock(template='tests/blocks/heading_block.html')),
            ('paragraph', blocks.CharBlock()),
        ], template='tests/blocks/stream_with_language.html')

        stream_value = block.to_python([
            {'type': 'heading', 'value': 'Bonjour'}
        ])

        result = render_to_string('tests/blocks/include_block_test.html', {
            'test_block': stream_value,
            'language': 'fr',
        })

        self.assertIn('<div class="heading" lang="fr"><h1 lang="fr">Bonjour</h1></div>', result)

    def test_include_block_tag_with_plain_value(self):
        """
        The include_block tag should be able to render a value without a render_as_block method
        by just rendering it as a string
        """
        result = render_to_string('tests/blocks/include_block_test.html', {
            'test_block': 42,
        })

        self.assertIn('<body>42</body>', result)

    def test_include_block_tag_with_filtered_value(self):
        """
        The block parameter on include_block tag should support complex values including filters,
        e.g. {% include_block foo|default:123 %}
        """
        block = blocks.CharBlock(template='tests/blocks/heading_block.html')
        bound_block = block.bind('bonjour')

        result = render_to_string('tests/blocks/include_block_test_with_filter.html', {
            'test_block': bound_block,
            'language': 'fr',
        })
        self.assertIn('<body><h1 lang="fr">bonjour</h1></body>', result)

        result = render_to_string('tests/blocks/include_block_test_with_filter.html', {
            'test_block': None,
            'language': 'fr',
        })
        self.assertIn('<body>999</body>', result)

    def test_include_block_tag_with_extra_context(self):
        """
        Test that it's possible to pass extra context on an include_block tag using
        {% include_block foo with classname="bar" %}
        """
        block = blocks.CharBlock(template='tests/blocks/heading_block.html')
        bound_block = block.bind('bonjour')

        result = render_to_string('tests/blocks/include_block_with_test.html', {
            'test_block': bound_block,
            'language': 'fr',
        })
        self.assertIn('<body><h1 lang="fr" class="important">bonjour</h1></body>', result)

    def test_include_block_tag_with_only_flag(self):
        """
        A tag such as {% include_block foo with classname="bar" only %}
        should not inherit the parent context
        """
        block = blocks.CharBlock(template='tests/blocks/heading_block.html')
        bound_block = block.bind('bonjour')

        result = render_to_string('tests/blocks/include_block_only_test.html', {
            'test_block': bound_block,
            'language': 'fr',
        })
        self.assertIn('<body><h1 class="important">bonjour</h1></body>', result)


class BlockUsingGetTemplateMethod(blocks.Block):

    my_new_template = "my_super_awesome_dynamic_template.html"

    def get_template(self):
        return self.my_new_template


class TestOverriddenGetTemplateBlockTag(TestCase):
    def test_template_is_overriden_by_get_template(self):

        block = BlockUsingGetTemplateMethod(template='tests/blocks/this_shouldnt_be_used.html')
        template = block.get_template()
        self.assertEqual(template, block.my_new_template)
