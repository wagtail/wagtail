from unittest import mock

from django.test import TestCase, override_settings

from wagtail.contrib.redirects.api.v3 import signal_handlers
from wagtail.contrib.redirects.models import Redirect


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
class TestRedirectCacheInvalidation(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        signal_handlers.register_signal_handlers()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        signal_handlers.unregister_signal_handlers()

    def test_create_redirect_doesnt_purge(self, purge):
        with self.captureOnCommitCallbacks(execute=True):
            Redirect.objects.create(old_path="/old", redirect_link="/new")

        purge.assert_not_called()

    def test_resave_redirect_purges(self, purge):
        redirect = Redirect.objects.create(old_path="/old", redirect_link="/new")

        with self.captureOnCommitCallbacks(execute=True):
            redirect.save()

        purge.assert_any_call(f"http://api.example.com/api/v3/redirects/{redirect.id}/")

    def test_delete_redirect_purges(self, purge):
        redirect = Redirect.objects.create(old_path="/old", redirect_link="/new")
        redirect_id = redirect.id

        with self.captureOnCommitCallbacks(execute=True):
            redirect.delete()

        purge.assert_any_call(f"http://api.example.com/api/v3/redirects/{redirect_id}/")
