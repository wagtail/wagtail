from django.core.exceptions import ValidationError
from django.http.request import HttpRequest
from django.test import TestCase, override_settings

from wagtail.core.models import Page, Site


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


@override_settings(ALLOWED_HOSTS=['localhost', 'events.example.com', 'about.example.com', 'unknown.site.com'])
class TestSiteRouting(TestCase):
    fixtures = ['test.json']
    find_for_request_queries_expected = 1

    def setUp(self):
        self.default_site = Site.objects.get(is_default_site=True)
        events_page = Page.objects.get(url_path='/home/events/')
        about_page = Page.objects.get(url_path='/home/about-us/')
        self.events_site = Site.objects.create(hostname='events.example.com', root_page=events_page)
        self.alternate_port_events_site = Site.objects.create(
            hostname='events.example.com',
            root_page=events_page,
            port='8765'
        )
        self.about_site = Site.objects.create(hostname='about.example.com', root_page=about_page)
        self.alternate_port_default_site = Site.objects.create(hostname=self.default_site.hostname, port='8765', root_page=self.default_site.root_page)
        self.unrecognised_port = '8000'
        self.unrecognised_hostname = 'unknown.site.com'

    def test_with_host(self):
        request = HttpRequest()
        request.META = {'HTTP_HOST': 'about.example.com'}
        self.assertEqual(Site.find_for_request(request), self.about_site)

    def test_with_server_name(self):
        request = HttpRequest()
        request.META = {
            'SERVER_NAME': 'about.example.com',
            'SERVER_PORT': 80
        }
        self.assertEqual(Site.find_for_request(request), self.about_site)

    @override_settings(USE_X_FORWARDED_HOST=True)
    def test_with_x_forwarded_host(self):
        request = HttpRequest()
        request.META = {'HTTP_X_FORWARDED_HOST': 'about.example.com'}
        self.assertEqual(Site.find_for_request(request), self.about_site)

    def test_no_host_header_routes_to_default_site(self):
        # requests without a Host: header should be directed to the default site
        request = HttpRequest()
        request.path = '/'
        with self.assertNumQueries(self.find_for_request_queries_expected):
            self.assertEqual(Site.find_for_request(request), self.default_site)

    def test_valid_headers_route_to_specific_site(self):
        # requests with a known Host: header should be directed to the specific site
        request = HttpRequest()
        request.path = '/'
        request.META['HTTP_HOST'] = self.events_site.hostname
        request.META['SERVER_PORT'] = self.events_site.port
        with self.assertNumQueries(self.find_for_request_queries_expected):
            self.assertEqual(Site.find_for_request(request), self.events_site)

    def test_ports_in_request_headers_are_respected(self):
        # ports in the Host: header should be respected
        request = HttpRequest()
        request.path = '/'
        request.META['HTTP_HOST'] = self.alternate_port_events_site.hostname
        request.META['SERVER_PORT'] = self.alternate_port_events_site.port
        with self.assertNumQueries(self.find_for_request_queries_expected):
            self.assertEqual(Site.find_for_request(request), self.alternate_port_events_site)

    def test_unrecognised_host_header_routes_to_default_site(self):
        # requests with an unrecognised Host: header should be directed to the
        # default site
        request = HttpRequest()
        request.path = '/'
        request.META['HTTP_HOST'] = self.unrecognised_hostname
        request.META['SERVER_PORT'] = '80'
        with self.assertNumQueries(self.find_for_request_queries_expected):
            self.assertEqual(Site.find_for_request(request), self.default_site)

    def test_unrecognised_host_header_raises_exception_when_no_default_site_is_set(self):
        # when the above test is repeated without a Site being marked as the
        # 'default', find_for_request() should raise an exception
        request = HttpRequest()
        request.path = '/'
        request.META['HTTP_HOST'] = self.unrecognised_hostname
        request.META['SERVER_PORT'] = '80'
        # unmark default_site as the default before calling
        self.default_site.is_default_site = False
        self.default_site.save()
        with self.assertRaises(Site.DoesNotExist):
            Site.find_for_request(request)

    def test_unrecognised_port_and_default_host_routes_to_default_site(self):
        # requests to the default host on an unrecognised port should be directed to the default site
        request = HttpRequest()
        request.path = '/'
        request.META['HTTP_HOST'] = self.default_site.hostname
        request.META['SERVER_PORT'] = self.unrecognised_port
        with self.assertNumQueries(self.find_for_request_queries_expected):
            self.assertEqual(Site.find_for_request(request), self.default_site)

    def test_unrecognised_port_and_unrecognised_host_routes_to_default_site(self):
        # requests with an unrecognised Host: header _and_ an unrecognised port
        # should be directed to the default site
        request = HttpRequest()
        request.path = '/'
        request.META['HTTP_HOST'] = self.unrecognised_hostname
        request.META['SERVER_PORT'] = self.unrecognised_port
        with self.assertNumQueries(self.find_for_request_queries_expected):
            self.assertEqual(Site.find_for_request(request), self.default_site)

    def test_unrecognised_port_and_unrecognised_host_raises_exception_when_no_default_site_is_set(self):
        # when the above test is repeated without a Site being marked as the
        # 'default', find_for_request() should raise an exception
        request = HttpRequest()
        request.path = '/'
        request.META['HTTP_HOST'] = self.unrecognised_hostname
        request.META['SERVER_PORT'] = self.unrecognised_port
        # unmark default_site as the default before calling
        self.default_site.is_default_site = False
        self.default_site.save()
        with self.assertRaises(Site.DoesNotExist):
            Site.find_for_request(request)

    def test_unrecognised_port_on_known_hostname_routes_there_if_no_ambiguity(self):
        # requests on an unrecognised port should be directed to the site with
        # matching hostname if there is no ambiguity
        request = HttpRequest()
        request.path = '/'
        request.META['HTTP_HOST'] = self.about_site.hostname
        request.META['SERVER_PORT'] = self.unrecognised_port
        with self.assertNumQueries(self.find_for_request_queries_expected):
            self.assertEqual(Site.find_for_request(request), self.about_site)

    def test_unrecognised_port_on_known_hostname_routes_to_default_site_if_ambiguity(self):
        # requests on an unrecognised port should be directed to the default
        # site, even if their hostname (but not port) matches more than one
        # other entry
        request = HttpRequest()
        request.path = '/'
        request.META['HTTP_HOST'] = self.events_site.hostname
        request.META['SERVER_PORT'] = self.unrecognised_port
        with self.assertNumQueries(self.find_for_request_queries_expected):
            self.assertEqual(Site.find_for_request(request), self.default_site)

    def test_port_in_http_host_header_is_ignored(self):
        # port in the HTTP_HOST header is ignored
        request = HttpRequest()
        request.path = '/'
        request.META['HTTP_HOST'] = "%s:%s" % (self.events_site.hostname, self.events_site.port)
        request.META['SERVER_PORT'] = self.alternate_port_events_site.port
        with self.assertNumQueries(self.find_for_request_queries_expected):
            self.assertEqual(Site.find_for_request(request), self.alternate_port_events_site)


@override_settings(
    WAGTAIL_SITE_CACHE_ENABLED=True,
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        },
    },
    ALLOWED_HOSTS=['localhost', 'events.example.com', 'about.example.com', 'unknown.site.com']
)
class TestSiteRoutingWithCachingEnabled(TestSiteRouting):
    find_for_request_queries_expected = 0

    def setUp(self):
        super().setUp()
        Site.objects.populate_cache()

    def test_clearing_cache_results_in_find_for_request_repopulating(self):
        Site.objects.clear_cache()
        request = HttpRequest()
        request.META = {'HTTP_HOST': 'about.example.com'}

        # It should take a single query to populate the cache again
        with self.assertNumQueries(1):
            self.assertEqual(Site.find_for_request(request), self.about_site)

        # Calling the same method again should create no queries now that
        # the cache is populated
        with self.assertNumQueries(0):
            self.assertEqual(Site.find_for_request(request), self.about_site)


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


class TestGetSiteRootPaths(TestCase):

    def setUp(self):
        self.default_site = Site.objects.get()
        self.abc_site = Site.objects.create(
            hostname='abc.com', root_page=self.default_site.root_page
        )
        self.def_site = Site.objects.create(
            hostname='def.com', root_page=self.default_site.root_page
        )

        # Changing the hostname to show that being the default site takes
        # promotes a site over the alphabetical ordering of hostname
        self.default_site.hostname = 'xyz.com'
        self.default_site.save()

    def test_result_order_when_multiple_sites_share_the_same_root_page(self):
        result = Site.get_site_root_paths()

        # An entry for the default site should come first
        self.assertEqual(result[0][0], self.default_site.id)

        # Followed by entries for others in 'host' alphabetical order
        self.assertEqual(result[1][0], self.abc_site.id)
        self.assertEqual(result[2][0], self.def_site.id)
