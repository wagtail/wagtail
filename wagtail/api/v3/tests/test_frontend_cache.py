from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import NoReverseMatch

from wagtail.api.v3 import signal_handlers
from wagtail.contrib.frontend_cache.backends.dummy import DummyBackend
from wagtail.test.utils import Page, PageFixturesMixin


@override_settings(
    WAGTAILFRONTENDCACHE={
        "dummy": {
            "BACKEND": "wagtail.contrib.frontend_cache.backends.dummy.DummyBackend",
        },
    },
    WAGTAILAPI_BASE_URL="http://api.example.com",
)
class TestPageCacheInvalidation(PageFixturesMixin, TestCase):
    fixtures = ["demosite.json"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        signal_handlers.register_signal_handlers()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        signal_handlers.unregister_signal_handlers()

    def setUp(self):
        DummyBackend.reset()

    def test_republish_page_purges(self):
        with self.captureOnCommitCallbacks(execute=True):
            Page.objects.get(id=2).specific.save_revision().publish()

        self.assertIn("http://api.example.com/api/v3/pages/2/", DummyBackend.urls)

    def test_unpublish_page_purges(self):
        with self.captureOnCommitCallbacks(execute=True):
            Page.objects.get(id=2).unpublish()

        self.assertIn("http://api.example.com/api/v3/pages/2/", DummyBackend.urls)

    def test_delete_page_purges(self):
        with self.captureOnCommitCallbacks(execute=True):
            Page.objects.get(id=16).delete()

        self.assertIn("http://api.example.com/api/v3/pages/16/", DummyBackend.urls)

    def test_save_draft_doesnt_purge(self):
        with self.captureOnCommitCallbacks(execute=True):
            Page.objects.get(id=2).specific.save_revision()

        self.assertEqual(DummyBackend.urls, [])

    @mock.patch("wagtail.api.v3.signal_handlers.reverse", side_effect=NoReverseMatch)
    def test_urls_not_mounted_doesnt_purge(self, reverse):
        with self.captureOnCommitCallbacks(execute=True):
            signal_handlers.purge_page_from_cache(Page.objects.get(id=2))

        reverse.assert_called_once()
        self.assertEqual(DummyBackend.urls, [])


class TestUseFrontendCache(SimpleTestCase):
    def test_disabled_by_default(self):
        self.assertFalse(signal_handlers.use_frontend_cache())

    @override_settings(WAGTAILAPI_USE_FRONTENDCACHE=True)
    def test_enabled(self):
        self.assertTrue(signal_handlers.use_frontend_cache())

    @override_settings(WAGTAILAPI_USE_FRONTENDCACHE=True)
    @mock.patch(
        "wagtail.api.v3.signal_handlers.apps.is_installed",
        side_effect=lambda app_name: app_name != "wagtail.contrib.frontend_cache",
    )
    def test_frontend_cache_not_installed(self, is_installed):
        with self.assertRaises(ImproperlyConfigured):
            signal_handlers.use_frontend_cache()

    @override_settings(WAGTAILAPI_USE_FRONTENDCACHE=True)
    @mock.patch(
        "wagtail.api.v3.signal_handlers.apps.is_installed",
        side_effect=lambda app_name: app_name != "wagtail.api.v3",
    )
    def test_api_v3_not_installed(self, is_installed):
        self.assertFalse(signal_handlers.use_frontend_cache())
