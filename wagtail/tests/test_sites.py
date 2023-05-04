from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from wagtail.coreutils import get_dummy_request
from wagtail.models import Page, Site


class TestSiteNaturalKey(TestCase):
    def test_natural_key(self):
        site = Site(hostname="example.com", port=8080)
        self.assertEqual(site.natural_key(), ("example.com", 8080))

    def test_get_by_natural_key(self):
        site = Site.objects.create(
            hostname="example.com", port=8080, root_page=Page.objects.get(pk=2)
        )
        self.assertEqual(Site.objects.get_by_natural_key("example.com", 8080), site)


class TestSiteUrl(TestCase):
    def test_root_url_http(self):
        site = Site(hostname="example.com", port=80)
        self.assertEqual(site.root_url, "http://example.com")

    def test_root_url_https(self):
        site = Site(hostname="example.com", port=443)
        self.assertEqual(site.root_url, "https://example.com")

    def test_root_url_custom_port(self):
        site = Site(hostname="example.com", port=8000)
        self.assertEqual(site.root_url, "http://example.com:8000")


class TestSiteNameDisplay(TestCase):
    def test_site_name_not_default(self):
        site = Site(
            hostname="example.com",
            port=80,
            site_name="example dot com",
            is_default_site=False,
        )
        self.assertEqual(site.__str__(), "example dot com")

    def test_site_name_default(self):
        site = Site(
            hostname="example.com",
            port=80,
            site_name="example dot com",
            is_default_site=True,
        )
        self.assertEqual(site.__str__(), "example dot com [default]")

    def test_no_site_name_not_default_port_80(self):
        site = Site(hostname="example.com", port=80, is_default_site=False)
        self.assertEqual(site.__str__(), "example.com")

    def test_no_site_name_default_port_80(self):
        site = Site(hostname="example.com", port=80, is_default_site=True)
        self.assertEqual(site.__str__(), "example.com [default]")

    def test_no_site_name_not_default_port_n(self):
        site = Site(hostname="example.com", port=8080, is_default_site=False)
        self.assertEqual(site.__str__(), "example.com:8080")

    def test_no_site_name_default_port_n(self):
        site = Site(hostname="example.com", port=8080, is_default_site=True)
        self.assertEqual(site.__str__(), "example.com:8080 [default]")


class TestSiteOrdering(TestCase):
    def setUp(self):
        self.root_page = Page.objects.get(pk=2)
        Site.objects.all().delete()  # Drop the initial site.

    def test_site_order_by_hostname(self):
        site_1 = Site.objects.create(hostname="charly.com", root_page=self.root_page)
        site_2 = Site.objects.create(hostname="bravo.com", root_page=self.root_page)
        site_3 = Site.objects.create(hostname="alfa.com", root_page=self.root_page)
        self.assertEqual(
            list(Site.objects.all().values_list("id", flat=True)),
            [site_3.id, site_2.id, site_1.id],
        )

    def test_site_order_by_hostname_upper(self):
        site_1 = Site.objects.create(hostname="charly.com", root_page=self.root_page)
        site_2 = Site.objects.create(hostname="Bravo.com", root_page=self.root_page)
        site_3 = Site.objects.create(hostname="alfa.com", root_page=self.root_page)
        self.assertEqual(
            list(Site.objects.all().values_list("id", flat=True)),
            [site_3.id, site_2.id, site_1.id],
        )

    def test_site_order_by_hostname_site_name_irrelevant(self):
        site_1 = Site.objects.create(
            hostname="charly.com", site_name="X-ray", root_page=self.root_page
        )
        site_2 = Site.objects.create(
            hostname="bravo.com", site_name="Yankee", root_page=self.root_page
        )
        site_3 = Site.objects.create(
            hostname="alfa.com", site_name="Zulu", root_page=self.root_page
        )
        self.assertEqual(
            list(Site.objects.all().values_list("id", flat=True)),
            [site_3.id, site_2.id, site_1.id],
        )


@override_settings(ALLOWED_HOSTS=["example.com", "unknown.com", "127.0.0.1", "[::1]"])
class TestFindSiteForRequest(TestCase):
    def setUp(self):
        self.default_site = Site.objects.get()
        self.site = Site.objects.create(
            hostname="example.com", port=80, root_page=Page.objects.get(pk=2)
        )

    def test_dummy_request(self):
        request = get_dummy_request(site=self.site)
        self.assertEqual(Site.find_for_request(request), self.site)

    def test_with_host(self):
        request = get_dummy_request()
        request.META.update({"HTTP_HOST": "example.com", "SERVER_PORT": 80})
        self.assertEqual(Site.find_for_request(request), self.site)

    def test_with_unknown_host(self):
        request = get_dummy_request()
        request.META.update({"HTTP_HOST": "unknown.com", "SERVER_PORT": 80})
        self.assertEqual(Site.find_for_request(request), self.default_site)

    def test_with_server_name(self):
        request = get_dummy_request()
        request.META.update({"SERVER_NAME": "example.com", "SERVER_PORT": 80})
        self.assertEqual(Site.find_for_request(request), self.site)

    def test_with_x_forwarded_host(self):
        with self.settings(USE_X_FORWARDED_HOST=True):
            request = get_dummy_request()
            request.META.update(
                {"HTTP_X_FORWARDED_HOST": "example.com", "SERVER_PORT": 80}
            )
            self.assertEqual(Site.find_for_request(request), self.site)

    def test_ipv4_host(self):
        request = get_dummy_request()
        request.META.update({"SERVER_NAME": "127.0.0.1", "SERVER_PORT": 80})
        self.assertEqual(Site.find_for_request(request), self.default_site)

    def test_ipv6_host(self):
        request = get_dummy_request()
        request.META.update({"SERVER_NAME": "[::1]", "SERVER_PORT": 80})
        self.assertEqual(Site.find_for_request(request), self.default_site)


class TestDefaultSite(TestCase):
    def test_create_default_site(self):
        Site.objects.all().delete()
        Site.objects.create(
            hostname="test.com", is_default_site=True, root_page=Page.objects.get(pk=2)
        )
        self.assertTrue(Site.objects.filter(is_default_site=True).exists())

    def test_change_default_site(self):
        default = Site.objects.get(is_default_site=True)
        default.is_default_site = False
        default.save()

        Site.objects.create(
            hostname="test.com", is_default_site=True, root_page=Page.objects.get(pk=2)
        )
        self.assertTrue(Site.objects.filter(is_default_site=True).exists())

    def test_there_can_only_be_one(self):
        site = Site(
            hostname="test.com", is_default_site=True, root_page=Page.objects.get(pk=2)
        )
        with self.assertRaises(ValidationError):
            site.clean_fields()

    def test_oops_there_is_more_than_one(self):
        Site.objects.create(
            hostname="example.com",
            is_default_site=True,
            root_page=Page.objects.get(pk=2),
        )

        site = Site(
            hostname="test.com", is_default_site=True, root_page=Page.objects.get(pk=2)
        )
        with self.assertRaises(Site.MultipleObjectsReturned):
            # If there already are multiple default sites, you're in trouble
            site.clean_fields()


class TestGetSiteRootPaths(TestCase):
    def setUp(self):
        self.default_site = Site.objects.get()
        self.abc_site = Site.objects.create(
            hostname="abc.com", root_page=self.default_site.root_page
        )
        self.def_site = Site.objects.create(
            hostname="def.com", root_page=self.default_site.root_page
        )

        # Changing the hostname to show that being the default site takes
        # promotes a site over the alphabetical ordering of hostname
        self.default_site.hostname = "xyz.com"
        self.default_site.save()

    def test_result_order_when_multiple_sites_share_the_same_root_page(self):
        result = Site.get_site_root_paths()

        # An entry for the default site should come first
        self.assertEqual(result[0][0], self.default_site.id)

        # Followed by entries for others in 'host' alphabetical order
        self.assertEqual(result[1][0], self.abc_site.id)
        self.assertEqual(result[2][0], self.def_site.id)


@override_settings(WAGTAIL_PER_THREAD_SITE_CACHING=True)
class TestSiteCache(TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        super().setUp()
        # Tests run in a shared thread, and loading of fixture data does not
        # trigger clearing of threadlocal caches. So, we manually clear them
        # here, so that cached site/root path values always reflect the data
        # in the fixture
        Site.clear_caches()

    def test_cache(self):
        # The cache should be empty to start with
        self.assertIsNone(Site.objects._get_cached_list())

        # Requesting the list should result in a database query
        with self.assertNumQueries(1):
            value = Site.objects.get_all()

        # Check return value matches expectations
        self.assertEqual(
            value,
            tuple(
                Site.objects.order_by(
                    "-root_page__url_path", "-is_default_site", "hostname"
                )
            ),
        )

        # Requesting again should return the cached value
        with self.assertNumQueries(0):
            second_value = Site.objects.get_all()

        # The returned tuples should be equal, but should not be the same tuple object
        self.assertEqual(value, second_value)
        self.assertIsNot(value, second_value)

    def test_cache_clears_when_site_saved(self):
        """
        This tests that the cache is cleared whenever a site is saved
        """
        # Trigger cache population
        Site.objects.get_all()

        # Check cache was populated
        self.assertIsNotNone(Site.objects._get_cached_list())

        # Save a site
        Site.objects.get(is_default_site=True).save()

        # Check the cache was cleared
        self.assertIsNone(Site.objects._get_cached_list())

    def test_cache_clears_when_site_deleted(self):
        """
        This tests that the cache is cleared whenever a site is deleted
        """
        # Trigger cache population
        Site.objects.get_all()

        # Check cache was populated
        self.assertIsNotNone(Site.objects._get_cached_list())

        # Delete a site
        Site.objects.get(is_default_site=True).delete()

        # Check the cache was cleared
        self.assertIsNone(Site.objects._get_cached_list())
