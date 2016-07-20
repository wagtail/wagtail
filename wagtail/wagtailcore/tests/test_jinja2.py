from __future__ import absolute_import, unicode_literals

from django.template import engines
from django.template.loader import render_to_string
from django.test import TestCase

from wagtail.wagtailcore import __version__, blocks
from wagtail.wagtailcore.models import Page, Site


class TestCoreJinja(TestCase):

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
