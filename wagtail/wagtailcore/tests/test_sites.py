from __future__ import absolute_import, unicode_literals

from django.core.exceptions import ValidationError
from django.http.request import HttpRequest
from django.test import TestCase

from wagtail.wagtailcore.models import Page, Site


class TestSiteNaturalKey(TestCase):
    def test_natural_key(self):
        site = Site(hostname='example.com', port=8080)
        self.assertEqual(site.natural_key(), ('example.com', 8080))

    def test_get_by_natural_key(self):
        site = Site.objects.create(hostname='example.com', port=8080, root_page=Page.objects.get(pk=2))
        self.assertEqual(Site.objects.get_by_natural_key('example.com', 8080),
                         site)


class TestSiteUrl(TestCase):
    def test_root_url_http(self):
        site = Site(hostname='example.com', port=80)
        self.assertEqual(site.root_url, 'http://example.com')

    def test_root_url_https(self):
        site = Site(hostname='example.com', port=443)
        self.assertEqual(site.root_url, 'https://example.com')

    def test_root_url_custom_port(self):
        site = Site(hostname='example.com', port=8000)
        self.assertEqual(site.root_url, 'http://example.com:8000')


class TestSiteNameDisplay(TestCase):
    def test_site_name_not_default(self):
        site = Site(hostname='example.com', port=80, site_name='example dot com', is_default_site=False)
        self.assertEqual(site.__str__(), 'example dot com')

    def test_site_name_default(self):
        site = Site(hostname='example.com', port=80, site_name='example dot com', is_default_site=True)
        self.assertEqual(site.__str__(), 'example dot com [default]')

    def test_no_site_name_not_default_port_80(self):
        site = Site(hostname='example.com', port=80, is_default_site=False)
        self.assertEqual(site.__str__(), 'example.com')

    def test_no_site_name_default_port_80(self):
        site = Site(hostname='example.com', port=80, is_default_site=True)
        self.assertEqual(site.__str__(), 'example.com [default]')

    def test_no_site_name_not_default_port_n(self):
        site = Site(hostname='example.com', port=8080, is_default_site=False)
        self.assertEqual(site.__str__(), 'example.com:8080')

    def test_no_site_name_default_port_n(self):
        site = Site(hostname='example.com', port=8080, is_default_site=True)
        self.assertEqual(site.__str__(), 'example.com:8080 [default]')


class TestFindSiteForRequest(TestCase):
    def setUp(self):
        self.default_site = Site.objects.get()
        self.site = Site.objects.create(hostname='example.com', port=80, root_page=Page.objects.get(pk=2))

    def test_default(self):
        request = HttpRequest()
        self.assertEqual(Site.find_for_request(request), self.default_site)

    def test_with_host(self):
        request = HttpRequest()
        request.META = {'HTTP_HOST': 'example.com'}
        self.assertEqual(Site.find_for_request(request), self.site)

    def test_with_unknown_host(self):
        request = HttpRequest()
        request.META = {'HTTP_HOST': 'unknown.com'}
        self.assertEqual(Site.find_for_request(request), self.default_site)

    def test_with_server_name(self):
        request = HttpRequest()
        request.META = {
            'SERVER_NAME': 'example.com',
            'SERVER_PORT': 80
        }
        self.assertEqual(Site.find_for_request(request), self.site)

    def test_with_x_forwarded_host(self):
        with self.settings(USE_X_FORWARDED_HOST=True):
            request = HttpRequest()
            request.META = {'HTTP_X_FORWARDED_HOST': 'example.com'}
            self.assertEqual(Site.find_for_request(request), self.site)


class TestDefaultSite(TestCase):
    def test_create_default_site(self):
        Site.objects.all().delete()
        Site.objects.create(hostname='test.com', is_default_site=True,
                            root_page=Page.objects.get(pk=2))
        self.assertTrue(Site.objects.filter(is_default_site=True).exists())

    def test_change_default_site(self):
        default = Site.objects.get(is_default_site=True)
        default.is_default_site = False
        default.save()

        Site.objects.create(hostname='test.com', is_default_site=True,
                            root_page=Page.objects.get(pk=2))
        self.assertTrue(Site.objects.filter(is_default_site=True).exists())

    def test_there_can_only_be_one(self):
        site = Site(hostname='test.com', is_default_site=True,
                    root_page=Page.objects.get(pk=2))
        with self.assertRaises(ValidationError):
            site.clean_fields()

    def test_oops_there_is_more_than_one(self):
        Site.objects.create(hostname='example.com', is_default_site=True,
                            root_page=Page.objects.get(pk=2))

        site = Site(hostname='test.com', is_default_site=True,
                    root_page=Page.objects.get(pk=2))
        with self.assertRaises(Site.MultipleObjectsReturned):
            # If there already are multiple default sites, you're in trouble
            site.clean_fields()
