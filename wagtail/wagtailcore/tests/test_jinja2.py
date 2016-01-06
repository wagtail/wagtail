from __future__ import absolute_import, unicode_literals

from django.template import engines
from django.test import TestCase

from wagtail.wagtailcore import __version__
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
