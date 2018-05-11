from django.template import engines
from django.template.loader import render_to_string
from django.test import TestCase

from wagtail import __version__
from wagtail.core import blocks
from wagtail.core.models import Page, Site
from wagtail.tests.testapp.blocks import SectionBlock


class TestCoreGlobalsAndFilters(TestCase):

    def setUp(self):
        self.engine = engines['jinja2']

    def render(self, string, context=None, request_context=True):
        if context is None:
            context = {}

        # Add a request to the template, to simulate a RequestContext
        if request_context:
            site = Site.objects.get(is_default_site=True)
            request = self.client.get('/test/', HTTP_HOST=site.hostname)
            request.site = site
            context['request'] = request

        template = self.engine.from_string(string)
        return template.render(context)

    def test_richtext(self):
        richtext = '<p>Merry <a linktype="page" id="2">Christmas</a>!</p>'
        self.assertEqual(
            self.render('{{ text|richtext }}', {'text': richtext}),
            '<div class="rich-text"><p>Merry <a href="/">Christmas</a>!</p></div>')

    def test_pageurl(self):
        page = Page.objects.get(pk=2)
        self.assertEqual(
            self.render('{{ pageurl(page) }}', {'page': page}),
            page.url)

    def test_slugurl(self):
        page = Page.objects.get(pk=2)
        self.assertEqual(
            self.render('{{ slugurl(page.slug) }}', {'page': page}),
            page.url)

    def test_bad_slugurl(self):
        self.assertEqual(
            self.render('{{ slugurl("bad-slug-doesnt-exist") }}', {}), 'None')

    def test_wagtail_version(self):
        self.assertEqual(
            self.render('{{ wagtail_version() }}'),
            __version__)


class TestJinjaEscaping(TestCase):
    fixtures = ['test.json']

    def test_block_render_result_is_safe(self):
        """
        Ensure that any results of template rendering in block.render are marked safe
        so that they don't get double-escaped when inserted into a parent template (#2541)
        """
        stream_block = blocks.StreamBlock([
            ('paragraph', blocks.CharBlock(template='tests/jinja2/paragraph.html'))
        ])

        stream_value = stream_block.to_python([
            {'type': 'paragraph', 'value': 'hello world'},
        ])

        result = render_to_string('tests/jinja2/stream.html', {
            'value': stream_value,
        })

        self.assertIn('<p>hello world</p>', result)

    def test_rich_text_is_safe(self):
        """
        Ensure that RichText values are marked safe
        so that they don't get double-escaped when inserted into a parent template (#2542)
        """
        stream_block = blocks.StreamBlock([
            ('paragraph', blocks.RichTextBlock(template='tests/jinja2/rich_text.html'))
        ])
        stream_value = stream_block.to_python([
            {'type': 'paragraph', 'value': '<p>Merry <a linktype="page" id="4">Christmas</a>!</p>'},
        ])

        result = render_to_string('tests/jinja2/stream.html', {
            'value': stream_value,
        })

        self.assertIn('<div class="rich-text"><p>Merry <a href="/events/christmas/">Christmas</a>!</p></div>', result)


class TestIncludeBlockTag(TestCase):
    def test_include_block_tag_with_boundblock(self):
        """
        The include_block tag should be able to render a BoundBlock's template
        while keeping the parent template's context
        """
        block = blocks.CharBlock(template='tests/jinja2/heading_block.html')
        bound_block = block.bind('bonjour')

        result = render_to_string('tests/jinja2/include_block_test.html', {
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

        result = render_to_string('tests/jinja2/include_block_test.html', {
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
            ('heading', blocks.CharBlock(template='tests/jinja2/heading_block.html')),
            ('paragraph', blocks.CharBlock()),
        ], template='tests/jinja2/stream_with_language.html')

        stream_value = block.to_python([
            {'type': 'heading', 'value': 'Bonjour'}
        ])

        result = render_to_string('tests/jinja2/include_block_test.html', {
            'test_block': stream_value,
            'language': 'fr',
        })

        self.assertIn('<div class="heading" lang="fr"><h1 lang="fr">Bonjour</h1></div>', result)

    def test_include_block_tag_with_plain_value(self):
        """
        The include_block tag should be able to render a value without a render_as_block method
        by just rendering it as a string
        """
        result = render_to_string('tests/jinja2/include_block_test.html', {
            'test_block': 42,
        })

        self.assertIn('<body>42</body>', result)

    def test_include_block_tag_with_filtered_value(self):
        """
        The block parameter on include_block tag should support complex values including filters,
        e.g. {% include_block foo|default:123 %}
        """
        block = blocks.CharBlock(template='tests/jinja2/heading_block.html')
        bound_block = block.bind('bonjour')

        result = render_to_string('tests/jinja2/include_block_test_with_filter.html', {
            'test_block': bound_block,
            'language': 'fr',
        })
        self.assertIn('<body><h1 lang="fr">bonjour</h1></body>', result)

        result = render_to_string('tests/jinja2/include_block_test_with_filter.html', {
            'test_block': None,
            'language': 'fr',
        })
        self.assertIn('<body>999</body>', result)
