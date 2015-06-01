import unittest

from django import forms
from django.forms.utils import ErrorList
from django.core.exceptions import ValidationError
from django.test import TestCase

from wagtail.wagtailcore import blocks
from wagtail.wagtailcore.rich_text import RichText
from wagtail.wagtailcore.models import Page

import base64


class TestFieldBlock(unittest.TestCase):
    def test_charfield_render(self):
        block = blocks.CharBlock()
        html = block.render("Hello world!")

        self.assertEqual(html, "Hello world!")

    def test_charfield_render_form(self):
        block = blocks.CharBlock()
        html = block.render_form("Hello world!")

        self.assertIn('<div class="field char_field widget-text_input">', html)
        self.assertIn('<input id="" name="" placeholder="" type="text" value="Hello world!" />', html)

    def test_charfield_render_form_with_prefix(self):
        block = blocks.CharBlock()
        html = block.render_form("Hello world!", prefix='foo')

        self.assertIn('<input id="foo" name="foo" placeholder="" type="text" value="Hello world!" />', html)

    def test_charfield_render_form_with_error(self):
        block = blocks.CharBlock()
        html = block.render_form("Hello world!",
            errors=ErrorList([ValidationError("This field is required.")])
        )

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
        self.assertIn('<select id="" name="" placeholder="">', html)
        self.assertIn('<option value="choice-1">Choice 1</option>', html)
        self.assertIn('<option value="choice-2" selected="selected">Choice 2</option>', html)

    @unittest.expectedFailure # Returning "choice-1" instead of "Choice 1"
    def test_choicefield_searchable_content(self):
        class ChoiceBlock(blocks.FieldBlock):
            field = forms.ChoiceField(choices=(
                ('choice-1', "Choice 1"),
                ('choice-2', "Choice 2"),
            ))

        block = ChoiceBlock()
        content = block.get_searchable_content("choice-1")

        self.assertEqual(content, ["Choice 1"])

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


class TestRichTextBlock(TestCase):
    fixtures = ['test.json']

    def test_get_default(self):
        default_value = blocks.RichTextBlock().get_default()
        self.assertTrue(isinstance(default_value, RichText))
        self.assertEqual(default_value.source, '')

        default_value = blocks.RichTextBlock(default=None).get_default()
        self.assertTrue(isinstance(default_value, RichText))
        self.assertEqual(default_value.source, '')

        default_value = blocks.RichTextBlock(default='').get_default()
        self.assertTrue(isinstance(default_value, RichText))
        self.assertEqual(default_value.source, '')

        default_value = blocks.RichTextBlock(default='<p>foo</p>').get_default()
        self.assertTrue(isinstance(default_value, RichText))
        self.assertEqual(default_value.source, '<p>foo</p>')

        default_value = blocks.RichTextBlock(default=RichText('<p>foo</p>')).get_default()
        self.assertTrue(isinstance(default_value, RichText))
        self.assertEqual(default_value.source, '<p>foo</p>')

    def test_render(self):
        block = blocks.RichTextBlock()
        value = RichText('<p>Merry <a linktype="page" id="4">Christmas</a>!</p>')
        result = block.render(value)
        self.assertEqual(result, '<div class="rich-text"><p>Merry <a href="/events/christmas/">Christmas</a>!</p></div>')

    def test_render_form(self):
        """
        render_form should produce the editor-specific rendition of the rich text value
        (which includes e.g. 'data-linktype' attributes on <a> elements)
        """
        block = blocks.RichTextBlock()
        value = RichText('<p>Merry <a linktype="page" id="4">Christmas</a>!</p>')
        result = block.render_form(value, prefix='richtext')
        self.assertIn('&lt;p&gt;Merry &lt;a data-linktype=&quot;page&quot; data-id=&quot;4&quot; href=&quot;/events/christmas/&quot;&gt;Christmas&lt;/a&gt;!&lt;/p&gt;', result)

    def test_validate_required_richtext_block(self):
        block = blocks.RichTextBlock()

        with self.assertRaises(ValidationError):
            block.clean(RichText(''))

    def test_validate_non_required_richtext_block(self):
        block = blocks.RichTextBlock(required=False)
        result = block.clean(RichText(''))
        self.assertTrue(isinstance(result, RichText))
        self.assertEqual(result.source, '')


class TestChoiceBlock(unittest.TestCase):
    def setUp(self):
        from django.db.models.fields import BLANK_CHOICE_DASH
        self.blank_choice_dash_label = BLANK_CHOICE_DASH[0][1]

    def test_render_required_choice_block(self):
        block = blocks.ChoiceBlock(choices=[('tea', 'Tea'), ('coffee', 'Coffee')])
        html = block.render_form('coffee', prefix='beverage')
        self.assertIn('<select id="beverage" name="beverage" placeholder="">', html)
        # blank option should still be rendered for required fields
        # (we may want it as an initial value)
        self.assertIn('<option value="">%s</option>' % self.blank_choice_dash_label, html)
        self.assertIn('<option value="tea">Tea</option>', html)
        self.assertIn('<option value="coffee" selected="selected">Coffee</option>', html)

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
        self.assertIn('<select id="beverage" name="beverage" placeholder="">', html)
        self.assertIn('<option value="">%s</option>' % self.blank_choice_dash_label, html)
        self.assertIn('<option value="tea">Tea</option>', html)
        self.assertIn('<option value="coffee" selected="selected">Coffee</option>', html)

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
        self.assertIn('<select id="beverage" name="beverage" placeholder="">', html)
        self.assertNotIn('<option value="">%s</option>' % self.blank_choice_dash_label, html)
        self.assertIn('<option value="" selected="selected">No thanks</option>', html)
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
        self.assertIn('<select id="beverage" name="beverage" placeholder="">', html)
        self.assertIn('<option value="" selected="selected">%s</option>' % self.blank_choice_dash_label, html)
        self.assertIn('<optgroup label="Alcoholic">', html)
        self.assertIn('<option value="tea">Tea</option>', html)

        # test rendering with a non-blank option selected
        html = block.render_form('tea', prefix='beverage')
        self.assertIn('<select id="beverage" name="beverage" placeholder="">', html)
        self.assertIn('<option value="">%s</option>' % self.blank_choice_dash_label, html)
        self.assertIn('<optgroup label="Alcoholic">', html)
        self.assertIn('<option value="tea" selected="selected">Tea</option>', html)

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
        self.assertIn('<select id="beverage" name="beverage" placeholder="">', html)
        self.assertNotIn('<option value="">%s</option>' % self.blank_choice_dash_label, html)
        self.assertNotIn('<option value="" selected="selected">%s</option>' % self.blank_choice_dash_label, html)
        self.assertIn('<optgroup label="Alcoholic">', html)
        self.assertIn('<option value="tea">Tea</option>', html)
        self.assertIn('<option value="" selected="selected">No thanks</option>', html)

        # test rendering with a non-blank option selected
        html = block.render_form('tea', prefix='beverage')
        self.assertIn('<select id="beverage" name="beverage" placeholder="">', html)
        self.assertNotIn('<option value="">%s</option>' % self.blank_choice_dash_label, html)
        self.assertNotIn('<option value="" selected="selected">%s</option>' % self.blank_choice_dash_label, html)
        self.assertIn('<optgroup label="Alcoholic">', html)
        self.assertIn('<option value="tea" selected="selected">Tea</option>', html)

    def test_subclassing(self):
        class BeverageChoiceBlock(blocks.ChoiceBlock):
            choices = [
                ('tea', 'Tea'),
                ('coffee', 'Coffee'),
            ]

        block = BeverageChoiceBlock(required=False)
        html = block.render_form('tea', prefix='beverage')
        self.assertIn('<select id="beverage" name="beverage" placeholder="">', html)
        self.assertIn('<option value="tea" selected="selected">Tea</option>', html)

        # subclasses of ChoiceBlock should deconstruct to a basic ChoiceBlock for migrations
        self.assertEqual(
            block.deconstruct(),
            (
                'wagtail.wagtailcore.blocks.ChoiceBlock',
                [],
                {
                    'choices': [('tea', 'Tea'), ('coffee', 'Coffee')],
                    'required': False,
                },
            )
        )


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

    def test_meta_multiple_inheritance(self):
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


class TestStructBlock(unittest.TestCase):
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

    @unittest.expectedFailure # Field order doesn't match inheritance order
    def test_initialisation_with_mixins(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            link = blocks.URLBlock()

        class StylingMixin(blocks.StructBlock):
            classname = blocks.CharBlock()

        class StyledLinkBlock(LinkBlock, StylingMixin):
            pass

        block = StyledLinkBlock()

        self.assertEqual(list(block.child_blocks.keys()), ['title', 'link', 'classname'])

    def test_render(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            link = blocks.URLBlock()

        block = LinkBlock()
        html = block.render({
            'title': "Wagtail site",
            'link': 'http://www.wagtail.io',
        })

        self.assertIn('<dt>title</dt>', html)
        self.assertIn('<dd>Wagtail site</dd>', html)
        self.assertIn('<dt>link</dt>', html)
        self.assertIn('<dd>http://www.wagtail.io</dd>', html)

    @unittest.expectedFailure
    def test_render_unknown_field(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            link = blocks.URLBlock()

        block = LinkBlock()
        html = block.render({
            'title': "Wagtail site",
            'link': 'http://www.wagtail.io',
            'image': 10,
        })

        self.assertIn('<dt>title</dt>', html)
        self.assertIn('<dd>Wagtail site</dd>', html)
        self.assertIn('<dt>link</dt>', html)
        self.assertIn('<dd>http://www.wagtail.io</dd>', html)

        # Don't render the extra item
        self.assertNotIn('<dt>image</dt>', html)

    def test_render_form(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            link = blocks.URLBlock()

        block = LinkBlock()
        html = block.render_form({
            'title': "Wagtail site",
            'link': 'http://www.wagtail.io',
        }, prefix='mylink')

        self.assertIn('<div class="struct-block">', html)
        self.assertIn('<div class="field char_field widget-text_input fieldname-title">', html)
        self.assertIn('<input id="mylink-title" name="mylink-title" placeholder="Title" type="text" value="Wagtail site" />', html)
        self.assertIn('<div class="field url_field widget-url_input fieldname-link">', html)
        self.assertIn('<input id="mylink-link" name="mylink-link" placeholder="Link" type="url" value="http://www.wagtail.io" />', html)

    def test_render_form_unknown_field(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            link = blocks.URLBlock()

        block = LinkBlock()
        html = block.render_form({
            'title': "Wagtail site",
            'link': 'http://www.wagtail.io',
            'image': 10,
        }, prefix='mylink')

        self.assertIn('<input id="mylink-title" name="mylink-title" placeholder="Title" type="text" value="Wagtail site" />', html)
        self.assertIn('<input id="mylink-link" name="mylink-link" placeholder="Link" type="url" value="http://www.wagtail.io" />', html)

        # Don't render the extra field
        self.assertNotIn('mylink-image', html)

    def test_render_form_uses_default_value(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock(default="Torchbox")
            link = blocks.URLBlock(default="http://www.torchbox.com")

        block = LinkBlock()
        html = block.render_form({}, prefix='mylink')

        self.assertIn('<input id="mylink-title" name="mylink-title" placeholder="Title" type="text" value="Torchbox" />', html)
        self.assertIn('<input id="mylink-link" name="mylink-link" placeholder="Link" type="url" value="http://www.torchbox.com" />', html)

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
        content = block.get_searchable_content({
            'title': "Wagtail site",
            'link': 'http://www.wagtail.io',
        })

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


class TestListBlock(unittest.TestCase):
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

        self.assertIn('<div class="sequence">', html)

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

        self.assertIn('<label for=links-0-value-title>Title</label>', html)
        self.assertIn('<label for=links-0-value-link>Link</label>', html)

    def test_render_form_values(self):
        html = self.render_form()

        self.assertIn('<input id="links-0-value-title" name="links-0-value-title" placeholder="Title" type="text" value="Wagtail" />', html)
        self.assertIn('<input id="links-0-value-link" name="links-0-value-link" placeholder="Link" type="url" value="http://www.wagtail.io" />', html)
        self.assertIn('<input id="links-1-value-title" name="links-1-value-title" placeholder="Title" type="text" value="Django" />', html)
        self.assertIn('<input id="links-1-value-link" name="links-1-value-link" placeholder="Link" type="url" value="http://www.djangoproject.com" />', html)

    def test_html_declarations(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            link = blocks.URLBlock()

        block = blocks.ListBlock(LinkBlock)
        html = block.html_declarations()

        self.assertIn('<input id="__PREFIX__-value-title" name="__PREFIX__-value-title" placeholder="Title" type="text" />', html)
        self.assertIn('<input id="__PREFIX__-value-link" name="__PREFIX__-value-link" placeholder="Link" type="url" />', html)

    def test_html_declarations_uses_default(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.CharBlock(default="Github")
            link = blocks.URLBlock(default="http://www.github.com")

        block = blocks.ListBlock(LinkBlock)
        html = block.html_declarations()

        self.assertIn('<input id="__PREFIX__-value-title" name="__PREFIX__-value-title" placeholder="Title" type="text" value="Github" />', html)
        self.assertIn('<input id="__PREFIX__-value-link" name="__PREFIX__-value-link" placeholder="Link" type="url" value="http://www.github.com" />', html)

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

        self.assertIn('<input type="hidden" name="shoppinglist-items-count" id="shoppinglist-items-count" value="3">', form_html)
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

        self.assertIn('<input type="hidden" name="shoppinglist-items-count" id="shoppinglist-items-count" value="1">', form_html)
        self.assertIn('value="chocolate"', form_html)


class TestStreamBlock(unittest.TestCase):
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

    @unittest.expectedFailure # Field order doesn't match inheritance order
    def test_initialisation_with_mixins(self):
        class ArticleBlock(blocks.StreamBlock):
            heading = blocks.CharBlock()
            paragraph = blocks.CharBlock()

        class IntroMixin(blocks.StreamBlock):
            intro = blocks.CharBlock()

        class ArticleWithIntroBlock(ArticleBlock, IntroMixin):
            pass

        block = ArticleWithIntroBlock()

        self.assertEqual(list(block.child_blocks.keys()), ['heading', 'paragraph', 'intro'])

    def render_article(self, data):
        class ArticleBlock(blocks.StreamBlock):
            heading = blocks.CharBlock()
            paragraph = blocks.RichTextBlock()

        block = ArticleBlock()
        value = block.to_python(data)

        return block.render(value)

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

    def render_form(self):
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
        return block.render_form(value, prefix='myarticle')

    def test_render_form_wrapper_class(self):
        html = self.render_form()

        self.assertIn('<div class="sequence">', html)

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

    def test_render_form_type_fields(self):
        html = self.render_form()

        self.assertIn('<input type="hidden" id="myarticle-0-type" name="myarticle-0-type" value="heading">', html)
        self.assertIn('<input type="hidden" id="myarticle-1-type" name="myarticle-1-type" value="paragraph">', html)
        self.assertIn('<input type="hidden" id="myarticle-2-type" name="myarticle-2-type" value="paragraph">', html)

    def test_render_form_value_fields(self):
        html = self.render_form()

        self.assertIn('<input id="myarticle-0-value" name="myarticle-0-value" placeholder="Heading" type="text" value="My title" />', html)
        self.assertIn('<input id="myarticle-1-value" name="myarticle-1-value" placeholder="Paragraph" type="text" value="My first paragraph" />', html)
        self.assertIn('<input id="myarticle-2-value" name="myarticle-2-value" placeholder="Paragraph" type="text" value="My second paragraph" />', html)

    def test_html_declarations(self):
        class ArticleBlock(blocks.StreamBlock):
            heading = blocks.CharBlock()
            paragraph = blocks.CharBlock()

        block = ArticleBlock()
        html = block.html_declarations()

        self.assertIn('<input id="__PREFIX__-value" name="__PREFIX__-value" placeholder="Heading" type="text" />', html)
        self.assertIn('<input id="__PREFIX__-value" name="__PREFIX__-value" placeholder="Paragraph" type="text" />', html)

    def test_html_declarations_uses_default(self):
        class ArticleBlock(blocks.StreamBlock):
            heading = blocks.CharBlock(default="Fish found on moon")
            paragraph = blocks.CharBlock(default="Lorem ipsum dolor sit amet")

        block = ArticleBlock()
        html = block.html_declarations()

        self.assertIn('<input id="__PREFIX__-value" name="__PREFIX__-value" placeholder="Heading" type="text" value="Fish found on moon" />', html)
        self.assertIn('<input id="__PREFIX__-value" name="__PREFIX__-value" placeholder="Paragraph" type="text" value="Lorem ipsum dolor sit amet" />', html)

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
                'article-%d-value' % i: "heading %d" % i
            })

        block_value = block.value_from_datadict(post_data, {}, 'article')
        self.assertEqual(block_value[2].value, "heading 0")

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
        block = blocks.PageChooserBlock()

        empty_form_html = block.render_form(None, 'page')
        self.assertIn('<input id="page" name="page" placeholder="" type="hidden" />', empty_form_html)

        christmas_page = Page.objects.get(slug='christmas')
        christmas_form_html = block.render_form(christmas_page, 'page')
        expected_html = '<input id="page" name="page" placeholder="" type="hidden" value="%d" />' % christmas_page.id
        self.assertIn(expected_html, christmas_form_html)

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
