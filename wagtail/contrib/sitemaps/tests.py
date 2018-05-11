import datetime

import pytz
from django.contrib.sites.shortcuts import get_current_site
from django.test import RequestFactory, TestCase

from wagtail.core.models import Page, PageViewRestriction, Site
from wagtail.tests.testapp.models import EventIndex, SimplePage

from .sitemap_generator import Sitemap


class TestSitemapGenerator(TestCase):
    def setUp(self):
        self.home_page = Page.objects.get(id=2)

        self.child_page = self.home_page.add_child(instance=SimplePage(
            title="Hello world!",
            slug='hello-world',
            content="hello",
            live=True,
            last_published_at=datetime.datetime(2017, 1, 1, 12, 0, 0, tzinfo=pytz.utc),
            latest_revision_created_at=datetime.datetime(2017, 2, 1, 12, 0, 0, tzinfo=pytz.utc)
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

        self.page_with_no_last_publish_date = self.home_page.add_child(instance=SimplePage(
            title="I have no last publish date :-(",
            slug='no-last-publish-date',
            content="hello",
            live=True,
            latest_revision_created_at=datetime.datetime(2017, 2, 1, 12, 0, 0, tzinfo=pytz.utc)
        ))

        self.site = Site.objects.get(is_default_site=True)

    def test_items(self):
        sitemap = Sitemap(self.site)
        pages = sitemap.items()

        self.assertIn(self.child_page.page_ptr.specific, pages)
        self.assertNotIn(self.unpublished_child_page.page_ptr.specific, pages)
        self.assertNotIn(self.protected_child_page.page_ptr.specific, pages)

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

    def test_lastmod_uses_last_published_date(self):
        request = RequestFactory().get('/sitemap.xml')
        req_protocol = request.scheme
        req_site = get_current_site(request)

        sitemap = Sitemap(self.site)
        urls = sitemap.get_urls(1, req_site, req_protocol)

        child_page_lastmod = [
            url['lastmod'] for url in urls
            if url['location'] == 'http://localhost/hello-world/'
        ][0]
        self.assertEqual(child_page_lastmod, datetime.datetime(2017, 1, 1, 12, 0, 0, tzinfo=pytz.utc))

        # if no last_publish_date is defined, use latest revision date
        child_page_lastmod = [
            url['lastmod'] for url in urls
            if url['location'] == 'http://localhost/no-last-publish-date/'
        ][0]
        self.assertEqual(child_page_lastmod, datetime.datetime(2017, 2, 1, 12, 0, 0, tzinfo=pytz.utc))

    def test_latest_lastmod(self):
        # give the homepage a lastmod
        self.home_page.last_published_at = datetime.datetime(2017, 3, 1, 12, 0, 0, tzinfo=pytz.utc)
        self.home_page.save()

        request = RequestFactory().get('/sitemap.xml')
        req_protocol = request.scheme
        req_site = get_current_site(request)

        sitemap = Sitemap(self.site)
        sitemap.get_urls(1, req_site, req_protocol)

        self.assertEqual(sitemap.latest_lastmod, datetime.datetime(2017, 3, 1, 12, 0, 0, tzinfo=pytz.utc))

    def test_latest_lastmod_missing(self):
        # ensure homepage does not have lastmod
        self.home_page.last_published_at = None
        self.home_page.save()

        request = RequestFactory().get('/sitemap.xml')
        req_protocol = request.scheme
        req_site = get_current_site(request)

        sitemap = Sitemap(self.site)
        sitemap.get_urls(1, req_site, req_protocol)

        self.assertFalse(hasattr(sitemap, 'latest_lastmod'))


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
