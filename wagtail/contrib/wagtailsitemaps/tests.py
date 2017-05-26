from __future__ import absolute_import, unicode_literals

from django.contrib.sites.shortcuts import get_current_site
from django.test import RequestFactory, TestCase

from wagtail.tests.testapp.models import EventIndex, SimplePage
from wagtail.wagtailcore.models import Page, PageViewRestriction, Site

from .sitemap_generator import Sitemap


class TestSitemapGenerator(TestCase):
    def setUp(self):
        self.home_page = Page.objects.get(id=2)

        self.child_page = self.home_page.add_child(instance=SimplePage(
            title="Hello world!",
            slug='hello-world',
            content="hello",
            live=True,
        ))

        self.unpublished_child_page = self.home_page.add_child(instance=SimplePage(
            title="Unpublished",
            slug='unpublished',
            content="hello",
            live=False,
        ))

        self.protected_child_page = self.home_page.add_child(instance=SimplePage(
            title="Protected",
            slug='protected',
            content="hello",
            live=True,
        ))
        PageViewRestriction.objects.create(page=self.protected_child_page, password='hello')

        self.site = Site.objects.get(is_default_site=True)

    def test_items(self):
        sitemap = Sitemap(self.site)
        pages = sitemap.items()

        self.assertIn(self.child_page.page_ptr, pages)
        self.assertNotIn(self.unpublished_child_page.page_ptr, pages)
        self.assertNotIn(self.protected_child_page.page_ptr, pages)

    def test_get_urls(self):
        request = RequestFactory().get('/sitemap.xml')
        req_protocol = request.scheme
        req_site = get_current_site(request)

        sitemap = Sitemap(self.site)
        urls = [url['location'] for url in sitemap.get_urls(1, req_site, req_protocol)]

        self.assertIn('http://localhost/', urls)  # Homepage
        self.assertIn('http://localhost/hello-world/', urls)  # Child page

    def test_get_urls_uses_specific(self):
        request = RequestFactory().get('/sitemap.xml')
        req_protocol = request.scheme
        req_site = get_current_site(request)

        # Add an event page which has an extra url in the sitemap
        self.home_page.add_child(instance=EventIndex(
            title="Events",
            slug='events',
            live=True,
        ))

        sitemap = Sitemap(self.site)
        urls = [url['location'] for url in sitemap.get_urls(1, req_site, req_protocol)]

        self.assertIn('http://localhost/events/', urls)  # Main view
        self.assertIn('http://localhost/events/past/', urls)  # Sub view


class TestIndexView(TestCase):
    def test_index_view(self):
        response = self.client.get('/sitemap-index.xml')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')


class TestSitemapView(TestCase):
    def test_sitemap_view(self):
        response = self.client.get('/sitemap.xml')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')
