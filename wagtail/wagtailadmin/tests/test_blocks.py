import unittest

from django import forms
from django.forms.utils import ErrorList
from django.core.exceptions import ValidationError

from wagtail.wagtailadmin import blocks


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


class TestListBlock(unittest.TestCase):
    def test_initialise_with_class(self):
        block = blocks.ListBlock(blocks.Block)

        # Child block should be initialised for us
        self.assertIsInstance(block.child_block, blocks.Block)

    def test_initialise_with_instance(self):
        child_block = blocks.Block()
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


class TestStreamBlock(unittest.TestCase):
    def test_initialisation(self):
        block = blocks.StreamBlock([
            ('heading', blocks.CharBlock()),
            ('paragraph', blocks.CharBlock()),
        ])

        self.assertEqual(list(block.child_blocks.keys()), ['heading', 'paragraph'])

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
            paragraph = blocks.CharBlock()

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
                'value': 'My first paragraph',
            },
            {
                'type': 'paragraph',
                'value': 'My second paragraph',
            },
        ])

        self.assertIn('<div class="block-heading">My title</div>', html)
        self.assertIn('<div class="block-paragraph">My first paragraph</div>', html)
        self.assertIn('<div class="block-paragraph">My second paragraph</div>', html)

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
        self.assertIn('<div class="block-paragraph">My first paragraph</div>', html)

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
        return block.render_form(value,  prefix='myarticle')

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

    def test_ordering_in_form_submission(self):
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
