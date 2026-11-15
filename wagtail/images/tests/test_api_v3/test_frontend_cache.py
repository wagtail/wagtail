from django.test import TestCase, override_settings

from wagtail.contrib.frontend_cache.backends.dummy import DummyBackend
from wagtail.images import get_image_model
from wagtail.images.api.v3 import signal_handlers
from wagtail.test.utils import PageFixturesMixin


@override_settings(
    WAGTAILFRONTENDCACHE={
        "dummy": {
            "BACKEND": "wagtail.contrib.frontend_cache.backends.dummy.DummyBackend",
        },
    },
    WAGTAILAPI_BASE_URL="http://api.example.com",
)
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

    def setUp(self):
        DummyBackend.reset()

    def test_resave_image_purges(self):
        with self.captureOnCommitCallbacks(execute=True):
            get_image_model().objects.get(id=5).save()

        self.assertIn("http://api.example.com/api/v3/images/5/", DummyBackend.urls)

    def test_delete_image_purges(self):
        with self.captureOnCommitCallbacks(execute=True):
            get_image_model().objects.get(id=5).delete()

        self.assertIn("http://api.example.com/api/v3/images/5/", DummyBackend.urls)
