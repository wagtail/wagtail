from unittest import mock

from django.test import TestCase, override_settings

from wagtail.images import get_image_model
from wagtail.images.api.v3 import signal_handlers
from wagtail.test.utils import PageFixturesMixin


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
class TestImageCacheInvalidation(PageFixturesMixin, TestCase):
    fixtures = ["demosite.json"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        signal_handlers.register_signal_handlers()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        signal_handlers.unregister_signal_handlers()

    def test_resave_image_purges(self, purge):
        with self.captureOnCommitCallbacks(execute=True):
            get_image_model().objects.get(id=5).save()

        purge.assert_any_call("http://api.example.com/api/v3/images/5/")

    def test_delete_image_purges(self, purge):
        with self.captureOnCommitCallbacks(execute=True):
            get_image_model().objects.get(id=5).delete()

        purge.assert_any_call("http://api.example.com/api/v3/images/5/")
