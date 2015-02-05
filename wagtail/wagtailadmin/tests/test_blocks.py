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

    def test_choicefield_render(self):
        block = blocks.FieldBlock(forms.ChoiceField(choices=(
            ('choice-1', "Choice 1"),
            ('choice-2', "Choice 2"),
        )))
        html = block.render('choice-2')

        self.assertEqual(html, "choice-2")

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


class TestStructBlock(unittest.TestCase):
    def test_initialisation(self):
        block = blocks.StructBlock([
            ('title', blocks.FieldBlock(forms.CharField())),
            ('link', blocks.FieldBlock(forms.URLField())),
        ])

        self.assertEqual(list(block.child_blocks.keys()), ['title', 'link'])

    def test_initialisation_from_subclass(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.FieldBlock(forms.CharField())
            link = blocks.FieldBlock(forms.URLField())

        block = LinkBlock()

        self.assertEqual(list(block.child_blocks.keys()), ['title', 'link'])

    def test_initialisation_from_subclass_with_extra(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.FieldBlock(forms.CharField())
            link = blocks.FieldBlock(forms.URLField())

        block = LinkBlock([
            ('classname', blocks.FieldBlock(forms.CharField()))
        ])

        self.assertEqual(list(block.child_blocks.keys()), ['title', 'link', 'classname'])

    def test_initialisation_with_multiple_subclassses(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.FieldBlock(forms.CharField())
            link = blocks.FieldBlock(forms.URLField())

        class StyledLinkBlock(LinkBlock):
            classname = blocks.FieldBlock(forms.CharField())

        block = StyledLinkBlock()

        self.assertEqual(list(block.child_blocks.keys()), ['title', 'link', 'classname'])

    @unittest.expectedFailure # Field order doesn't match inheritance order
    def test_initialisation_with_mixins(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.FieldBlock(forms.CharField())
            link = blocks.FieldBlock(forms.URLField())

        class StylingMixin(blocks.StructBlock):
            classname = blocks.FieldBlock(forms.CharField())

        class StyledLinkBlock(LinkBlock, StylingMixin):
            pass

        block = StyledLinkBlock()

        self.assertEqual(list(block.child_blocks.keys()), ['title', 'link', 'classname'])

    def test_render(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.FieldBlock(forms.CharField(label="Title"))
            link = blocks.FieldBlock(forms.URLField(label="Link"))

        block = LinkBlock()
        html = block.render({
            'title': "Wagtail site",
            'link': 'http://www.wagtail.io',
        })

        self.assertIn('<dt>title</dt>', html)
        self.assertIn('<dd>Wagtail site</dd>', html)
        self.assertIn('<dt>link</dt>', html)
        self.assertIn('<dd>http://www.wagtail.io</dd>', html)

    def test_render_form(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.FieldBlock(forms.CharField())
            link = blocks.FieldBlock(forms.URLField())

        block = LinkBlock()
        html = block.render_form({
            'title': "Wagtail site",
            'link': 'http://www.wagtail.io',
        }, prefix='mylink')

        self.assertIn('<div class="struct-block">', html)
        self.assertIn('<div class="field char_field">', html)
        self.assertIn('<input id="mylink-title" name="mylink-title" type="text" value="Wagtail site" />', html)
        self.assertIn('<div class="field url_field">', html)
        self.assertIn('<input id="mylink-link" name="mylink-link" type="url" value="http://www.wagtail.io" />', html)


class TestListBlock(unittest.TestCase):
    def test_initialise_with_class(self):
        block = blocks.ListBlock(blocks.Block)

        # Child block should be initialised for us
        self.assertIsInstance(block.child_block, blocks.Block)

    def test_initialise_with_instance(self):
        child_block = blocks.Block()
        block = blocks.ListBlock(child_block)

        self.assertEqual(block.child_block, child_block)

    def render_form(self):
        class LinkBlock(blocks.StructBlock):
            title = blocks.FieldBlock(forms.CharField())
            link = blocks.FieldBlock(forms.URLField())

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
        ]
        , prefix='links')

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
        self.assertIn('<label for=links-1-value-link>Link</label>', html)

    def test_render_form_values(self):
        html = self.render_form()

        self.assertIn('<input id="links-0-value-title" name="links-0-value-title" type="text" value="Wagtail" />', html)
        self.assertIn('<input id="links-0-value-link" name="links-0-value-link" type="url" value="http://www.wagtail.io" />', html)
        self.assertIn('<input id="links-1-value-title" name="links-1-value-title" type="text" value="Django" />', html)
        self.assertIn('<input id="links-1-value-link" name="links-1-value-link" type="url" value="http://www.djangoproject.com" />', html)
