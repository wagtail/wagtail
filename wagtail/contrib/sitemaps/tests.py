from django.test import TestCase
from django.core.cache import cache

from wagtail.wagtailcore.models import Page, PageViewRestriction, Site
from wagtail.tests.testapp.models import SimplePage, EventIndex

from .sitemap_generator import Sitemap


class TestSitemapGenerator(TestCase):
    def setUp(self):
        self.home_page = Page.objects.get(id=2)

        self.child_page = self.home_page.add_child(instance=SimplePage(
            title="Hello world!",
            slug='hello-world',
            live=True,
        ))

        self.unpublished_child_page = self.home_page.add_child(instance=SimplePage(
            title="Unpublished",
            slug='unpublished',
            live=False,
        ))

        self.protected_child_page = self.home_page.add_child(instance=SimplePage(
            title="Protected",
            slug='protected',
            live=True,
        ))
        PageViewRestriction.objects.create(page=self.protected_child_page, password='hello')

        self.site = Site.objects.get(is_default_site=True)

    def test_get_pages(self):
        sitemap = Sitemap(self.site)
        pages = sitemap.get_pages()

        self.assertIn(self.child_page.page_ptr, pages)
        self.assertNotIn(self.unpublished_child_page.page_ptr, pages)
        self.assertNotIn(self.protected_child_page.page_ptr, pages)

    def test_get_urls(self):
        sitemap = Sitemap(self.site)
        urls = [url['location'] for url in sitemap.get_urls()]

        self.assertIn('http://localhost/', urls)  # Homepage
        self.assertIn('http://localhost/hello-world/', urls)  # Child page

    def test_get_urls_uses_specific(self):
        # Add an event page which has an extra url in the sitemap
        self.home_page.add_child(instance=EventIndex(
            title="Events",
            slug='events',
            live=True,
        ))

        sitemap = Sitemap(self.site)
        urls = [url['location'] for url in sitemap.get_urls()]

        self.assertIn('http://localhost/events/', urls)  # Main view
        self.assertIn('http://localhost/events/past/', urls)  # Sub view

    def test_render(self):
        sitemap = Sitemap(self.site)
        xml = sitemap.render()

        # Check that a URL has made it into the xml
        self.assertIn('http://localhost/hello-world/', xml)

        # Make sure the unpublished page didn't make it into the xml
        self.assertNotIn('http://localhost/unpublished/', xml)

        # Make sure the protected page didn't make it into the xml
        self.assertNotIn('http://localhost/protected/', xml)


class TestSitemapView(TestCase):
    def test_sitemap_view(self):
        response = self.client.get('/sitemap.xml')

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsitemaps/sitemap.xml')
        self.assertEqual(response['Content-Type'], 'text/xml; charset=utf-8')

    def test_sitemap_view_cache(self):
        cache_key = 'wagtail-sitemap:%d' % Site.objects.get(is_default_site=True).id

        # Check that the key is not in the cache
        self.assertNotIn(cache_key, cache)

        # Hit the view
        first_response = self.client.get('/sitemap.xml')

        self.assertEqual(first_response.status_code, 200)
        self.assertTemplateUsed(first_response, 'wagtailsitemaps/sitemap.xml')

        # Check that the key is in the cache
        self.assertIn(cache_key, cache)

        # Hit the view again. Should come from the cache this time
        second_response = self.client.get('/sitemap.xml')

        self.assertEqual(second_response.status_code, 200)
        self.assertTemplateNotUsed(second_response, 'wagtailsitemaps/sitemap.xml')  # Sitemap should not be re rendered

        # Check that the content is the same
        self.assertEqual(first_response.content, second_response.content)
