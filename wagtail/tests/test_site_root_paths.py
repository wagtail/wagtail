from django.test import TestCase
from django.test.utils import override_settings

from wagtail.models import Locale, Page, Site, SiteRootPath
from wagtail.test.testapp.models import SimplePage


@override_settings(WAGTAIL_PER_THREAD_SITE_CACHING=True)
class TestSiteRootPathsCache(TestCase):
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
        self.assertIsNone(Site._get_cached_site_root_paths())

        # Requesting the list should result in a database query
        with self.assertNumQueries(1):
            value = Site.get_site_root_paths()

        # Check return value matches expectations
        self.assertEqual(
            value,
            [
                SiteRootPath(
                    site_id=1,
                    root_path="/home/",
                    root_url="http://localhost",
                    language_code="en",
                )
            ],
        )

        # Requesting again should return the cached value
        with self.assertNumQueries(0):
            second_value = Site.get_site_root_paths()

        # Return values should be equal, but should not be the same object
        self.assertEqual(value, second_value)
        self.assertIsNot(value, second_value)

    def test_cache_clears_when_site_saved(self):
        """
        Tests that the cache is cleared whenever a site is saved
        """
        # Trigger cache population
        Site.get_site_root_paths()

        # Check the cache was populated
        self.assertIsNotNone(Site._get_cached_site_root_paths())

        # Save a site
        Site.objects.get(is_default_site=True).save()

        # Check the cache was cleared
        self.assertIsNone(Site._get_cached_site_root_paths())

    def test_cache_clears_when_site_deleted(self):
        """
        Tests that the cache is cleared whenever a site is deleted
        """
        # Trigger cache population
        Site.get_site_root_paths()

        # Check the cache was populated
        self.assertIsNotNone(Site._get_cached_site_root_paths())

        # Delete a site
        Site.objects.get(is_default_site=True).delete()

        # Check the cache was cleared
        self.assertIsNone(Site._get_cached_site_root_paths())

    def test_cache_clears_when_site_root_moves(self):
        """
        Tests that the cahce is cleared when a site root page is moved to a different
        part of the page tree, changing it's `path` value.
        """
        # Trigger cache population
        Site.get_site_root_paths()

        # Check site and root path caches were populated
        self.assertIsNotNone(Site.objects._get_cached_list())
        self.assertIsNotNone(Site._get_cached_site_root_paths())

        # Get homepage, root page and site
        root_page = Page.objects.get(id=1)
        homepage = Page.objects.get(url_path="/home/")
        default_site = Site.objects.get(is_default_site=True)

        # Create a new homepage under current homepage
        new_homepage = SimplePage(
            title="New Homepage", slug="new-homepage", content="hello"
        )
        homepage.add_child(instance=new_homepage)

        # Set new homepage as the site root page
        default_site.root_page = new_homepage
        default_site.save()

        # Move new homepage to root
        new_homepage.move(root_page, pos="last-child")

        # Check the caches were cleared
        self.assertIsNone(Site.objects._get_cached_list())
        self.assertIsNone(Site._get_cached_site_root_paths())

    def test_cache_clears_when_site_root_slug_changes(self):
        """
        Tests that the cache is cleared when a site root page's slug value
        is changed.
        """
        # Trigger cache population
        Site.get_site_root_paths()

        # Check site and root path caches were populated
        self.assertIsNotNone(Site.objects._get_cached_list())
        self.assertIsNotNone(Site._get_cached_site_root_paths())

        # Get homepage
        homepage = Page.objects.get(url_path="/home/")

        # Change slug
        homepage.slug = "new-home"
        homepage.save()

        # Check the caches were cleared
        self.assertIsNone(Site.objects._get_cached_list())
        self.assertIsNone(Site._get_cached_site_root_paths())

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_cache_clears_when_site_root_is_translated(self):
        """
        Tests that the cache is cleared when a site root page is translated
        to a different language, creating a 'root path' for the target language.
        """

        # Trigger cache population
        Site.get_site_root_paths()

        # Check site and root path caches were populated
        self.assertIsNotNone(Site.objects._get_cached_list())
        self.assertIsNotNone(Site._get_cached_site_root_paths())

        # Get homepage
        homepage = Page.objects.get(url_path="/home/")

        # Translate the homepage
        homepage.copy_for_translation(Locale.objects.create(language_code="fr"))

        # Check the caches were cleared
        self.assertIsNone(Site.objects._get_cached_list())
        self.assertIsNone(Site._get_cached_site_root_paths())

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_cache_clears_when_site_root_is_translated_as_alias(self):
        """
        Tests that the cache is cleared when a site root page is translated
        to a different language using the alias=True option. The new page
        should still create 'root path' for the target language.
        """

        # Trigger cache population
        Site.get_site_root_paths()

        # Check site and root path caches were populated
        self.assertIsNotNone(Site.objects._get_cached_list())
        self.assertIsNotNone(Site._get_cached_site_root_paths())

        # Get homepage
        homepage = Page.objects.get(url_path="/home/")

        # Translate the homepage
        homepage.copy_for_translation(
            Locale.objects.create(language_code="fr"), alias=True
        )

        # Check the caches were cleared
        self.assertIsNone(Site.objects._get_cached_list())
        self.assertIsNone(Site._get_cached_site_root_paths())
