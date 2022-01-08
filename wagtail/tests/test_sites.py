from django.core.exceptions import ValidationError
from django.http.request import HttpRequest
from django.test import TestCase, override_settings

from wagtail.models import Locale, Page, Site, SiteRootPath


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

    def test_with_host(self):
        request = HttpRequest()
        request.META = {"HTTP_HOST": "example.com", "SERVER_PORT": 80}
        self.assertEqual(Site.find_for_request(request), self.site)

    def test_with_unknown_host(self):
        request = HttpRequest()
        request.META = {"HTTP_HOST": "unknown.com", "SERVER_PORT": 80}
        self.assertEqual(Site.find_for_request(request), self.default_site)

    def test_with_server_name(self):
        request = HttpRequest()
        request.META = {"SERVER_NAME": "example.com", "SERVER_PORT": 80}
        self.assertEqual(Site.find_for_request(request), self.site)

    def test_with_x_forwarded_host(self):
        with self.settings(USE_X_FORWARDED_HOST=True):
            request = HttpRequest()
            request.META = {"HTTP_X_FORWARDED_HOST": "example.com", "SERVER_PORT": 80}
            self.assertEqual(Site.find_for_request(request), self.site)

    def test_ipv4_host(self):
        request = HttpRequest()
        request.META = {"SERVER_NAME": "127.0.0.1", "SERVER_PORT": 80}
        self.assertEqual(Site.find_for_request(request), self.default_site)

    def test_ipv6_host(self):
        request = HttpRequest()
        request.META = {"SERVER_NAME": "[::1]", "SERVER_PORT": 80}
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


class TestRootPathMethods(TestCase):
    def setUp(self):
        self.no_content_language_code = "ja"
        self.site = Site.objects.select_related(
            "root_page", "root_page__locale"
        ).first()
        self.english_root_path = SiteRootPath(
            self.site.id, "/home/", "http://localhost", "en"
        )

    @override_settings(WAGTAIL_I18N_ENABLED=False)
    def test_with_wagtail_i18n_disabled(self):
        # If 'root_page' and 'root_page__locale' are prefetched with `select_related`,
        # using any of the root path methods should not result in further queries
        with self.assertNumQueries(0):
            self.assertEqual(self.site.default_root_path, self.english_root_path)
            self.assertEqual(self.site.root_paths, [self.english_root_path])
            self.assertEqual(self.site.root_paths(), [self.english_root_path])
            # Tests for get_root_path()
            for value in (
                None,
                "",
                self.no_content_language_code,
                "en",
                "fr",
            ):
                with self.subTest(value):
                    self.assertEqual(
                        self.site.get_root_path(value), self.english_root_path
                    )

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_without_alternative_languages_roots(self):

        # If 'root_page' and 'root_page__locale' are prefetched with `select_related`,
        # getting the default root path shouldn't require a database query
        with self.assertNumQueries(0):
            self.assertEqual(self.site.default_root_path, self.english_root_path)

        # But, getting all potential root paths will trigger a lookup for
        # translated root pages
        with self.assertNumQueries(1):
            self.assertEqual(self.site.root_paths, [self.english_root_path])

        # get_root_path() should reuse the value returned by the `root_paths`
        # cached_property above
        with self.assertNumQueries(0):
            for value in (
                None,
                "",
                self.no_content_language_code,
                "en",
                "fr",
            ):
                with self.subTest(value):
                    self.assertEqual(
                        self.site.get_root_path(value), self.english_root_path
                    )

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_with_alternative_language_roots(self):
        # set up some alternative locales
        french_locale = Locale.objects.create(language_code="fr")
        thai_locale = Locale.objects.create(language_code="th")
        bengali_locale = Locale.objects.create(language_code="bn")

        # create some translated versions of the site root
        # These are deliberately created in non-alphabetical order to demonstrate
        # that translated site root paths are returned in `Page.path` order
        self.site.root_page.copy_for_translation(french_locale)
        self.site.root_page.copy_for_translation(thai_locale)
        bengali_version = self.site.root_page.copy_for_translation(bengali_locale)

        # these are for use in equality checks below
        french_root_path = SiteRootPath(
            self.site.pk, "/home-fr/", "http://localhost", "fr"
        )
        bengali_root_path = SiteRootPath(
            self.site.pk, "/home-bn/", "http://localhost", "bn"
        )
        thai_root_path = SiteRootPath(
            self.site.pk, "/home-th/", "http://localhost", "th"
        )

        # the 'default' root path should be for the Site's `root_page`,
        # and retrieving it shouldn't require a database query if
        # 'root_page' and 'root_page__locale' have been prefetched
        with self.assertNumQueries(0):
            default_root_path = self.site.default_root_path
            self.assertEqual(default_root_path, self.english_root_path)

        # When using 'root_paths', the 'default' root path
        # should come first, followed by the translated versions in 'path' order
        with self.assertNumQueries(1):
            self.assertEqual(
                self.site.root_paths,
                [
                    default_root_path,
                    french_root_path,
                    thai_root_path,
                    bengali_root_path,
                ],
            )

        # if we move the original site root to last place,
        # it will still appear first, because it's the site root
        original_version = self.site.root_page
        parent_page = original_version.get_parent()
        original_version.move(parent_page, pos="last-child")
        self.assertEqual(
            self.site.root_paths(),
            [default_root_path, french_root_path, thai_root_path, bengali_root_path],
        )

        # if we move the bengali version page to first place,
        # it should appear after the default, but before the other
        # translated versions
        bengali_version.move(parent_page, pos="first-child")
        self.assertEqual(
            self.site.root_paths(),
            [default_root_path, bengali_root_path, french_root_path, thai_root_path],
        )

        # Tests for get_root_path()
        for value, expected_result in (
            (None, default_root_path),
            ("", default_root_path),
            (self.no_content_language_code, default_root_path),
            ("en", default_root_path),
            ("fr", french_root_path),
            ("bn", bengali_root_path),
        ):
            with self.subTest(value):
                self.assertEqual(self.site.get_root_path(value), expected_result)


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
