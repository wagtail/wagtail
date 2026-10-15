from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import NoReverseMatch

from wagtail.api.v3 import signal_handlers
from wagtail.test.utils import Page, PageFixturesMixin


@override_settings(
    WAGTAILFRONTENDCACHE={
        "varnish": {
            "BACKEND": "wagtail.contrib.frontend_cache.backends.HTTPBackend",
            "LOCATION": "http://localhost:8000",
        },
    },
    WAGTAILAPI_BASE_URL="http://api.example.com",
)
@mock.patch("wagtail.contrib.frontend_cache.backends.http.HTTPBackend.purge")
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

    def test_republish_page_purges(self, purge):
        with self.captureOnCommitCallbacks(execute=True):
            Page.objects.get(id=2).specific.save_revision().publish()

        purge.assert_any_call("http://api.example.com/api/v3/pages/2/")

    def test_unpublish_page_purges(self, purge):
        with self.captureOnCommitCallbacks(execute=True):
            Page.objects.get(id=2).unpublish()

        purge.assert_any_call("http://api.example.com/api/v3/pages/2/")

    def test_delete_page_purges(self, purge):
        with self.captureOnCommitCallbacks(execute=True):
            Page.objects.get(id=16).delete()

        purge.assert_any_call("http://api.example.com/api/v3/pages/16/")

    def test_save_draft_doesnt_purge(self, purge):
        with self.captureOnCommitCallbacks(execute=True):
            Page.objects.get(id=2).specific.save_revision()

        purge.assert_not_called()

    @mock.patch("wagtail.api.v3.signal_handlers.reverse", side_effect=NoReverseMatch)
    def test_urls_not_mounted_doesnt_purge(self, reverse, purge):
        with self.captureOnCommitCallbacks(execute=True):
            signal_handlers.purge_page_from_cache(Page.objects.get(id=2))

        reverse.assert_called_once()
        purge.assert_not_called()


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
