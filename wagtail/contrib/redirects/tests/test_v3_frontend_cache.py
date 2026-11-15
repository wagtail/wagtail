from django.test import TestCase, override_settings

from wagtail.contrib.frontend_cache.backends.dummy import DummyBackend
from wagtail.contrib.redirects.api.v3 import signal_handlers
from wagtail.contrib.redirects.models import Redirect


@override_settings(
    WAGTAILFRONTENDCACHE={
        "dummy": {
            "BACKEND": "wagtail.contrib.frontend_cache.backends.dummy.DummyBackend",
        },
    },
    WAGTAILAPI_BASE_URL="http://api.example.com",
)
class TestRedirectCacheInvalidation(TestCase):
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

    def test_create_redirect_doesnt_purge(self):
        with self.captureOnCommitCallbacks(execute=True):
            Redirect.objects.create(old_path="/old", redirect_link="/new")

        self.assertEqual(DummyBackend.urls, [])

    def test_resave_redirect_purges(self):
        redirect = Redirect.objects.create(old_path="/old", redirect_link="/new")

        with self.captureOnCommitCallbacks(execute=True):
            redirect.save()

        self.assertIn(
            f"http://api.example.com/api/v3/redirects/{redirect.id}/", DummyBackend.urls
        )

    def test_delete_redirect_purges(self):
        redirect = Redirect.objects.create(old_path="/old", redirect_link="/new")
        redirect_id = redirect.id

        with self.captureOnCommitCallbacks(execute=True):
            redirect.delete()

        self.assertIn(
            f"http://api.example.com/api/v3/redirects/{redirect_id}/", DummyBackend.urls
        )
