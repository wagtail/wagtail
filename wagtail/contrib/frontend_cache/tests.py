from unittest import mock
from urllib.error import HTTPError, URLError

import requests
from azure.mgmt.cdn import CdnManagementClient
from azure.mgmt.frontdoor import FrontDoorManagementClient
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase
from django.test.utils import override_settings

from wagtail.contrib.frontend_cache.backends import (
    AzureCdnBackend,
    AzureFrontDoorBackend,
    BaseBackend,
    CloudflareBackend,
    CloudfrontBackend,
    HTTPBackend,
)
from wagtail.contrib.frontend_cache.utils import get_backends
from wagtail.models import Page
from wagtail.test.testapp.models import EventIndex, EventPage

from .utils import (
    PurgeBatch,
    purge_page_from_cache,
    purge_pages_from_cache,
    purge_url_from_cache,
    purge_urls_from_cache,
)

EVENTPAGE_URLS = {
    "http://localhost/events/final-event/",
    "http://localhost/events/christmas/",
    "http://localhost/events/saint-patrick/",
    "http://localhost/events/tentative-unpublished-event/",
    "http://localhost/events/someone-elses-event/",
    "http://localhost/events/tentative-unpublished-event/",
    "http://localhost/secret-plans/steal-underpants/",
}


class TestBackendConfiguration(SimpleTestCase):
    def test_default(self):
        backends = get_backends()

        self.assertEqual(len(backends), 0)

    def test_varnish(self):
        backends = get_backends(
            backend_settings={
                "varnish": {
                    "BACKEND": "wagtail.contrib.frontend_cache.backends.HTTPBackend",
                    "LOCATION": "http://localhost:8000",
                },
            }
        )

        self.assertEqual(set(backends.keys()), {"varnish"})
        self.assertIsInstance(backends["varnish"], HTTPBackend)

        self.assertEqual(backends["varnish"].cache_scheme, "http")
        self.assertEqual(backends["varnish"].cache_netloc, "localhost:8000")

    def test_cloudflare(self):
        backends = get_backends(
            backend_settings={
                "cloudflare": {
                    "BACKEND": "wagtail.contrib.frontend_cache.backends.CloudflareBackend",
                    "EMAIL": "test@test.com",
                    "API_KEY": "this is the api key",
                    "ZONEID": "this is a zone id",
                    "BEARER_TOKEN": "this is a bearer token",
                },
            }
        )

        self.assertEqual(set(backends.keys()), {"cloudflare"})
        self.assertIsInstance(backends["cloudflare"], CloudflareBackend)

        self.assertEqual(backends["cloudflare"].cloudflare_email, "test@test.com")
        self.assertEqual(
            backends["cloudflare"].cloudflare_api_key, "this is the api key"
        )
        self.assertEqual(
            backends["cloudflare"].cloudflare_token, "this is a bearer token"
        )

    def test_cloudfront(self):
        backends = get_backends(
            backend_settings={
                "cloudfront": {
                    "BACKEND": "wagtail.contrib.frontend_cache.backends.CloudfrontBackend",
                    "DISTRIBUTION_ID": "frontend",
                    "AWS_ACCESS_KEY_ID": "my-access-key-id",
                    "AWS_SECRET_ACCESS_KEY": "my-secret-access-key",
                },
            }
        )

        self.assertEqual(set(backends.keys()), {"cloudfront"})
        self.assertIsInstance(backends["cloudfront"], CloudfrontBackend)

        self.assertEqual(backends["cloudfront"].cloudfront_distribution_id, "frontend")

        credentials = backends["cloudfront"].client._request_signer._credentials

        self.assertEqual(credentials.method, "explicit")
        self.assertEqual(credentials.access_key, "my-access-key-id")
        self.assertEqual(credentials.secret_key, "my-secret-access-key")

    def test_azure_cdn(self):
        backends = get_backends(
            backend_settings={
                "azure_cdn": {
                    "BACKEND": "wagtail.contrib.frontend_cache.backends.AzureCdnBackend",
                    "RESOURCE_GROUP_NAME": "test-resource-group",
                    "CDN_PROFILE_NAME": "wagtail-io-profile",
                    "CDN_ENDPOINT_NAME": "wagtail-io-endpoint",
                },
            }
        )

        self.assertEqual(set(backends.keys()), {"azure_cdn"})
        self.assertIsInstance(backends["azure_cdn"], AzureCdnBackend)
        self.assertEqual(
            backends["azure_cdn"]._resource_group_name, "test-resource-group"
        )
        self.assertEqual(backends["azure_cdn"]._cdn_profile_name, "wagtail-io-profile")
        self.assertEqual(
            backends["azure_cdn"]._cdn_endpoint_name, "wagtail-io-endpoint"
        )

    def test_azure_front_door(self):
        backends = get_backends(
            backend_settings={
                "azure_front_door": {
                    "BACKEND": "wagtail.contrib.frontend_cache.backends.AzureFrontDoorBackend",
                    "RESOURCE_GROUP_NAME": "test-resource-group",
                    "FRONT_DOOR_NAME": "wagtail-io-front-door",
                },
            }
        )

        self.assertEqual(set(backends.keys()), {"azure_front_door"})
        self.assertIsInstance(backends["azure_front_door"], AzureFrontDoorBackend)
        self.assertEqual(
            backends["azure_front_door"]._resource_group_name, "test-resource-group"
        )
        self.assertEqual(
            backends["azure_front_door"]._front_door_name, "wagtail-io-front-door"
        )

    def test_azure_cdn_get_client(self):
        mock_credentials = mock.MagicMock()
        backends = get_backends(
            backend_settings={
                "azure_cdn": {
                    "BACKEND": "wagtail.contrib.frontend_cache.backends.AzureCdnBackend",
                    "RESOURCE_GROUP_NAME": "test-resource-group",
                    "CDN_PROFILE_NAME": "wagtail-io-profile",
                    "CDN_ENDPOINT_NAME": "wagtail-io-endpoint",
                    "SUBSCRIPTION_ID": "fake-subscription-id",
                    "CREDENTIALS": mock_credentials,
                },
            }
        )
        self.assertEqual(set(backends.keys()), {"azure_cdn"})
        client = backends["azure_cdn"]._get_client()
        self.assertIsInstance(client, CdnManagementClient)
        self.assertEqual(client._config.subscription_id, "fake-subscription-id")
        self.assertIs(client._config.credential, mock_credentials)

    def test_azure_front_door_get_client(self):
        mock_credentials = mock.MagicMock()
        backends = get_backends(
            backend_settings={
                "azure_front_door": {
                    "BACKEND": "wagtail.contrib.frontend_cache.backends.AzureFrontDoorBackend",
                    "RESOURCE_GROUP_NAME": "test-resource-group",
                    "FRONT_DOOR_NAME": "wagtail-io-fake-front-door-name",
                    "SUBSCRIPTION_ID": "fake-subscription-id",
                    "CREDENTIALS": mock_credentials,
                },
            }
        )
        client = backends["azure_front_door"]._get_client()
        self.assertEqual(set(backends.keys()), {"azure_front_door"})
        self.assertIsInstance(client, FrontDoorManagementClient)
        self.assertEqual(client._config.subscription_id, "fake-subscription-id")
        self.assertIs(client._config.credential, mock_credentials)

    @mock.patch(
        "wagtail.contrib.frontend_cache.backends.azure.AzureCdnBackend._make_purge_call"
    )
    def test_azure_cdn_purge(self, make_purge_call_mock):
        backends = get_backends(
            backend_settings={
                "azure_cdn": {
                    "BACKEND": "wagtail.contrib.frontend_cache.backends.AzureCdnBackend",
                    "RESOURCE_GROUP_NAME": "test-resource-group",
                    "CDN_PROFILE_NAME": "wagtail-io-profile",
                    "CDN_ENDPOINT_NAME": "wagtail-io-endpoint",
                    "CREDENTIALS": "Fake credentials",
                },
            }
        )

        self.assertEqual(set(backends.keys()), {"azure_cdn"})
        self.assertIsInstance(backends["azure_cdn"], AzureCdnBackend)

        # purge()
        backends["azure_cdn"].purge(
            "http://www.wagtail.org/home/events/christmas/?test=1"
        )
        make_purge_call_mock.assert_called_once()
        call_args = tuple(make_purge_call_mock.call_args)[0]
        self.assertEqual(len(call_args), 2)
        self.assertIsInstance(call_args[0], CdnManagementClient)
        self.assertEqual(call_args[1], ["/home/events/christmas/?test=1"])
        make_purge_call_mock.reset_mock()

        # purge_batch()
        backends["azure_cdn"].purge_batch(
            [
                "http://www.wagtail.org/home/events/christmas/?test=1",
                "http://torchbox.com/blog/",
            ]
        )
        make_purge_call_mock.assert_called_once()
        call_args = tuple(make_purge_call_mock.call_args)[0]
        self.assertIsInstance(call_args[0], CdnManagementClient)
        self.assertEqual(call_args[1], ["/home/events/christmas/?test=1", "/blog/"])

    @mock.patch(
        "wagtail.contrib.frontend_cache.backends.azure.AzureFrontDoorBackend._make_purge_call"
    )
    def test_azure_front_door_purge(self, make_purge_call_mock):
        backends = get_backends(
            backend_settings={
                "azure_front_door": {
                    "BACKEND": "wagtail.contrib.frontend_cache.backends.AzureFrontDoorBackend",
                    "RESOURCE_GROUP_NAME": "test-resource-group",
                    "FRONT_DOOR_NAME": "wagtail-io-front-door",
                    "CREDENTIALS": "Fake credentials",
                },
            }
        )

        self.assertEqual(set(backends.keys()), {"azure_front_door"})
        self.assertIsInstance(backends["azure_front_door"], AzureFrontDoorBackend)

        # purge()
        backends["azure_front_door"].purge(
            "http://www.wagtail.org/home/events/christmas/?test=1"
        )
        make_purge_call_mock.assert_called_once()
        call_args = tuple(make_purge_call_mock.call_args)[0]
        self.assertIsInstance(call_args[0], FrontDoorManagementClient)
        self.assertEqual(call_args[1], ["/home/events/christmas/?test=1"])

        make_purge_call_mock.reset_mock()

        # purge_batch()
        backends["azure_front_door"].purge_batch(
            [
                "http://www.wagtail.org/home/events/christmas/?test=1",
                "http://torchbox.com/blog/",
            ]
        )
        make_purge_call_mock.assert_called_once()
        call_args = tuple(make_purge_call_mock.call_args)[0]
        self.assertIsInstance(call_args[0], FrontDoorManagementClient)
        self.assertEqual(call_args[1], ["/home/events/christmas/?test=1", "/blog/"])

    def test_http(self):
        """Test that `HTTPBackend.purge` works when urlopen succeeds"""
        self._test_http_with_side_effect(urlopen_side_effect=None)

    def test_http_httperror(self):
        """Test that `HTTPBackend.purge` can handle `HTTPError`"""
        http_error = HTTPError(
            url="http://localhost:8000/home/events/christmas/",
            code=500,
            msg="Internal Server Error",
            hdrs={},
            fp=None,
        )
        with self.assertLogs(level="ERROR") as log_output:
            self._test_http_with_side_effect(urlopen_side_effect=http_error)

        self.assertIn(
            "Couldn't purge 'http://www.wagtail.org/home/events/christmas/' from HTTP cache. HTTPError: 500 Internal Server Error",
            log_output.output[0],
        )

    def test_http_urlerror(self):
        """Test that `HTTPBackend.purge` can handle `URLError`"""
        url_error = URLError(reason="just for tests")
        with self.assertLogs(level="ERROR") as log_output:
            self._test_http_with_side_effect(urlopen_side_effect=url_error)
        self.assertIn(
            "Couldn't purge 'http://www.wagtail.org/home/events/christmas/' from HTTP cache. URLError: just for tests",
            log_output.output[0],
        )

    @mock.patch("wagtail.contrib.frontend_cache.backends.http.urlopen")
    def _test_http_with_side_effect(self, urlopen_mock, urlopen_side_effect):
        # given a backends configuration with one HTTP backend
        backends = get_backends(
            backend_settings={
                "varnish": {
                    "BACKEND": "wagtail.contrib.frontend_cache.backends.HTTPBackend",
                    "LOCATION": "http://localhost:8000",
                },
            }
        )
        self.assertEqual(set(backends.keys()), {"varnish"})
        self.assertIsInstance(backends["varnish"], HTTPBackend)
        # and mocked urlopen that may or may not raise network-related exception
        urlopen_mock.side_effect = urlopen_side_effect

        # when making a purge request
        backends.get("varnish").purge("http://www.wagtail.org/home/events/christmas/")

        # then no exception is raised
        # and mocked urlopen is called with a proper purge request
        self.assertEqual(urlopen_mock.call_count, 1)
        (purge_request,), _call_kwargs = urlopen_mock.call_args
        self.assertEqual(
            purge_request.full_url, "http://localhost:8000/home/events/christmas/"
        )

    def test_cloudfront_validate_distribution_id(self):
        with self.assertRaises(ImproperlyConfigured):
            get_backends(
                backend_settings={
                    "cloudfront": {
                        "BACKEND": "wagtail.contrib.frontend_cache.backends.CloudfrontBackend",
                    },
                }
            )

    @mock.patch(
        "wagtail.contrib.frontend_cache.backends.cloudfront.CloudfrontBackend._create_invalidation"
    )
    def test_cloudfront_purge_with_query_string(self, mock_create_invalidation):
        """Test that CloudFront invalidation includes query strings when purging URLs."""
        backends = get_backends(
            backend_settings={
                "cloudfront": {
                    "BACKEND": "wagtail.contrib.frontend_cache.backends.CloudfrontBackend",
                    "DISTRIBUTION_ID": "frontend",
                    "AWS_ACCESS_KEY_ID": "test-access-key",
                    "AWS_SECRET_ACCESS_KEY": "test-secret-key",
                },
            }
        )

        backends["cloudfront"].purge(
            "http://www.example.com/path/to/page?query=value&another=param"
        )
        mock_create_invalidation.assert_called_once_with(
            "frontend", ["/path/to/page?query=value&another=param"]
        )

    @mock.patch(
        "wagtail.contrib.frontend_cache.backends.cloudfront.CloudfrontBackend._create_invalidation"
    )
    def test_cloudfront_purge_root_with_query_string(self, mock_create_invalidation):
        """Test that CloudFront invalidation handles root URLs with query strings."""
        backends = get_backends(
            backend_settings={
                "cloudfront": {
                    "BACKEND": "wagtail.contrib.frontend_cache.backends.CloudfrontBackend",
                    "DISTRIBUTION_ID": "frontend",
                    "AWS_ACCESS_KEY_ID": "test-access-key",
                    "AWS_SECRET_ACCESS_KEY": "test-secret-key",
                },
            }
        )

        backends["cloudfront"].purge("http://www.example.com?query=value")
        mock_create_invalidation.assert_called_once_with("frontend", ["/?query=value"])

    @mock.patch(
        "wagtail.contrib.frontend_cache.backends.cloudfront.CloudfrontBackend._create_invalidation"
    )
    def test_cloudfront_purge_batch_with_query_strings(self, mock_create_invalidation):
        """Test that CloudFront invalidation batch includes query strings."""
        backends = get_backends(
            backend_settings={
                "cloudfront": {
                    "BACKEND": "wagtail.contrib.frontend_cache.backends.CloudfrontBackend",
                    "DISTRIBUTION_ID": "frontend",
                    "AWS_ACCESS_KEY_ID": "test-access-key",
                    "AWS_SECRET_ACCESS_KEY": "test-secret-key",
                },
            }
        )

        backends["cloudfront"].purge_batch(
            [
                "http://www.example.com/path/to/page?query=value",
                "http://www.example.com/another/path",
                "http://www.example.com?root=query",
            ]
        )
        mock_create_invalidation.assert_called_once()
        self.assertEqual(mock_create_invalidation.call_args.args[0], "frontend")
        self.assertEqual(
            sorted(mock_create_invalidation.call_args.args[1]),
            ["/?root=query", "/another/path", "/path/to/page?query=value"],
        )

    def test_multiple(self):
        backends = get_backends(
            backend_settings={
                "varnish": {
                    "BACKEND": "wagtail.contrib.frontend_cache.backends.HTTPBackend",
                    "LOCATION": "http://localhost:8000/",
                },
                "cloudflare": {
                    "BACKEND": "wagtail.contrib.frontend_cache.backends.CloudflareBackend",
                    "EMAIL": "test@test.com",
                    "API_KEY": "this is the api key",
                    "ZONEID": "this is a zone id",
                },
            }
        )

        self.assertEqual(set(backends.keys()), {"varnish", "cloudflare"})

    def test_filter(self):
        backends = get_backends(
            backend_settings={
                "varnish": {
                    "BACKEND": "wagtail.contrib.frontend_cache.backends.HTTPBackend",
                    "LOCATION": "http://localhost:8000/",
                },
                "cloudflare": {
                    "BACKEND": "wagtail.contrib.frontend_cache.backends.CloudflareBackend",
                    "EMAIL": "test@test.com",
                    "API_KEY": "this is the api key",
                    "ZONEID": "this is a zone id",
                },
            },
            backends=["cloudflare"],
        )

        self.assertEqual(set(backends.keys()), {"cloudflare"})

    @override_settings(WAGTAILFRONTENDCACHE_LOCATION="http://localhost:8000")
    def test_backwards_compatibility(self):
        backends = get_backends()

        self.assertEqual(set(backends.keys()), {"default"})
        self.assertIsInstance(backends["default"], HTTPBackend)
        self.assertEqual(backends["default"].cache_scheme, "http")
        self.assertEqual(backends["default"].cache_netloc, "localhost:8000")


PURGED_URLS = set()


class MockBackend(BaseBackend):
    def purge(self, url):
        PURGED_URLS.add(url)


class MockCloudflareBackend(CloudflareBackend):
    def _purge_urls(self, urls):
        if len(urls) > self.CHUNK_SIZE:
            raise Exception("Cloudflare backend is not chunking requests as expected")

        PURGED_URLS.update(urls)


@override_settings(
    WAGTAILFRONTENDCACHE={
        "varnish": {
            "BACKEND": "wagtail.contrib.frontend_cache.tests.MockBackend",
        },
    },
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }
    },
)
class TestCachePurgingFunctions(TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        PURGED_URLS.clear()

    def test_purge_url_from_cache(self):
        with self.captureOnCommitCallbacks(execute=True):
            purge_url_from_cache("http://localhost/foo")
        self.assertEqual(PURGED_URLS, {"http://localhost/foo"})

    def test_purge_urls_from_cache(self):
        with self.captureOnCommitCallbacks(execute=True):
            purge_urls_from_cache(["http://localhost/foo", "http://localhost/bar"])
        self.assertEqual(PURGED_URLS, {"http://localhost/foo", "http://localhost/bar"})

    def test_purge_page_from_cache(self):
        page = EventIndex.objects.get(url_path="/home/events/")
        with self.captureOnCommitCallbacks(execute=True):
            with self.assertNumQueries(1):
                # Because no cache object is provided, a query is needed to
                # fetch site root paths in order to derive page urls
                purge_page_from_cache(page)
        self.assertEqual(
            PURGED_URLS,
            {"http://localhost/events/", "http://localhost/events/past/"},
        )

    def test_purge_page_from_cache_with_shared_cache_object(self):
        page = EventIndex.objects.get(url_path="/home/events/")

        # Ensure site root paths are already cached, which should result in
        # zero additional queries being incurred by this test
        page._get_relevant_site_root_paths()

        with self.captureOnCommitCallbacks(execute=True):
            # Because site root paths are already available via the cache_object,
            # no further queries should be needed to derive page urls
            with self.assertNumQueries(0):
                purge_page_from_cache(page, cache_object=page)

        self.assertEqual(
            PURGED_URLS,
            {"http://localhost/events/", "http://localhost/events/past/"},
        )

    def test_purge_pages_from_cache(self):
        pages = list(Page.objects.all().type(EventPage))
        with self.captureOnCommitCallbacks(execute=True):
            with self.assertNumQueries(1):
                # Because no cache object is provided, a query is needed to
                # fetch site root paths in order to derive page urls
                purge_pages_from_cache(pages)
        self.assertEqual(PURGED_URLS, EVENTPAGE_URLS)

    def test_purge_pages_from_cache_with_shared_cache_object(self):
        pages = list(Page.objects.all().type(EventPage))

        # Use the first page as the cache object for the operation
        cache_object = pages[0]

        # Ensure site root paths are already cached, which should result in
        # zero additional queries being incurred by this test
        cache_object._get_relevant_site_root_paths()

        with self.captureOnCommitCallbacks(execute=True):
            # Because site root paths are already available via the cache_object,
            # no further queries should be needed to derive page urls
            with self.assertNumQueries(0):
                purge_pages_from_cache(pages, cache_object=cache_object)

        self.assertEqual(PURGED_URLS, EVENTPAGE_URLS)

    def test_purge_batch(self):
        page = EventIndex.objects.get(url_path="/home/events/")
        batch = PurgeBatch()

        # Because no cache object is provided, a query is needed to
        # fetch site root paths in order to derive page urls
        with self.assertNumQueries(1):
            batch.add_page(page)

        batch.add_url("http://localhost/foo")

        with self.captureOnCommitCallbacks(execute=True):
            batch.purge()

        self.assertEqual(
            PURGED_URLS,
            {
                "http://localhost/events/",
                "http://localhost/events/past/",
                "http://localhost/foo",
            },
        )

    def test_purge_batch_with_multiple_pages(self):
        pages = list(Page.objects.all().type(EventPage))
        batch = PurgeBatch()

        # Because the batch has no cache object, a query is needed to
        # fetch site root paths in order to derive page urls
        with self.assertNumQueries(1):
            batch.add_pages(pages)

        with self.captureOnCommitCallbacks(execute=True):
            batch.purge()

        self.assertEqual(PURGED_URLS, EVENTPAGE_URLS)

    def test_multiple_purge_batches_with_shared_cache_object(self):
        pages = list(Page.objects.all().type(EventPage))

        # Use the first page as the cache object for the batch
        cache_object = pages[0]

        # Ensure site root paths are already cached, which should result in
        # zero additional queries being incurred by this test
        cache_object._get_relevant_site_root_paths()

        batch = PurgeBatch(cache_object=cache_object)

        with self.assertNumQueries(0):
            # Because site root paths are already available via the cache_object,
            # no queries should be needed to derive page urls
            batch.add_pages(pages)

        with self.captureOnCommitCallbacks(execute=True):
            batch.purge()

        self.assertEqual(PURGED_URLS, EVENTPAGE_URLS)
        PURGED_URLS.clear()

    @override_settings(
        WAGTAILFRONTENDCACHE={
            "varnish": {
                "BACKEND": "wagtail.contrib.frontend_cache.tests.MockBackend",
                "HOSTNAMES": ["example.com"],
            },
        }
    )
    def test_invalidate_specific_location(self):
        with self.assertLogs(level="INFO") as log_output:
            with self.captureOnCommitCallbacks(execute=True):
                purge_url_from_cache("http://localhost/foo")

        self.assertEqual(PURGED_URLS, set())
        self.assertIn(
            "Unable to find purge backend for localhost",
            log_output.output[0],
        )

        with self.captureOnCommitCallbacks(execute=True):
            purge_url_from_cache("http://example.com/foo")
        self.assertEqual(PURGED_URLS, {"http://example.com/foo"})


@override_settings(
    WAGTAILFRONTENDCACHE={
        "cloudflare": {
            "BACKEND": "wagtail.contrib.frontend_cache.tests.MockCloudflareBackend",
            "ZONEID": "zone",
            "BEARER_TOKEN": "token",
        },
    }
)
class TestCloudflareCachePurgingFunctions(TestCase):
    def setUp(self):
        # Reset PURGED_URLS to an empty list
        PURGED_URLS.clear()

    def test_cloudflare_purge_batch_chunked(self):
        with self.captureOnCommitCallbacks(execute=True):
            batch = PurgeBatch()
            urls = [f"https://localhost/foo{i}" for i in range(1, 65)]
            batch.add_urls(urls)
            batch.purge()

        self.assertCountEqual(PURGED_URLS, set(urls))


@override_settings(
    WAGTAILFRONTENDCACHE={
        "varnish": {
            "BACKEND": "wagtail.contrib.frontend_cache.tests.MockBackend",
        },
    }
)
class TestCachePurgingSignals(TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        # Reset PURGED_URLS to an empty list
        PURGED_URLS.clear()

    def test_purge_on_publish(self):
        with self.captureOnCommitCallbacks(execute=True):
            page = EventIndex.objects.get(url_path="/home/events/")
            page.save_revision().publish()
        self.assertEqual(
            PURGED_URLS, {"http://localhost/events/", "http://localhost/events/past/"}
        )

    def test_purge_on_unpublish(self):
        with self.captureOnCommitCallbacks(execute=True):
            page = EventIndex.objects.get(url_path="/home/events/")
            page.unpublish()
        self.assertEqual(
            PURGED_URLS, {"http://localhost/events/", "http://localhost/events/past/"}
        )

    def test_purge_with_unroutable_page(self):
        with self.captureOnCommitCallbacks(execute=True):
            root = Page.objects.get(url_path="/")
            page = EventIndex(title="new top-level page")
            root.add_child(instance=page)
            page.save_revision().publish()
        self.assertEqual(PURGED_URLS, set())

    @override_settings(
        ROOT_URLCONF="wagtail.test.urls_multilang",
        LANGUAGE_CODE="en",
        WAGTAILFRONTENDCACHE_LANGUAGES=["en", "fr", "pt-br"],
    )
    def test_purge_on_publish_in_multilang_env(self):
        with self.captureOnCommitCallbacks(execute=True):
            page = EventIndex.objects.get(url_path="/home/events/")
            page.save_revision().publish()

        self.assertEqual(
            PURGED_URLS,
            {
                "http://localhost/en/events/",
                "http://localhost/en/events/past/",
                "http://localhost/fr/events/",
                "http://localhost/fr/events/past/",
                "http://localhost/pt-br/events/",
                "http://localhost/pt-br/events/past/",
            },
        )

    @override_settings(
        ROOT_URLCONF="wagtail.test.urls_multilang",
        LANGUAGE_CODE="en",
        WAGTAIL_I18N_ENABLED=True,
        WAGTAIL_CONTENT_LANGUAGES=[("en", "English"), ("fr", "French")],
    )
    def test_purge_on_publish_with_i18n_enabled(self):
        with self.captureOnCommitCallbacks(execute=True):
            page = EventIndex.objects.get(url_path="/home/events/")
            page.save_revision().publish()

        self.assertEqual(
            PURGED_URLS,
            {
                "http://localhost/en/events/",
                "http://localhost/en/events/past/",
                "http://localhost/fr/events/",
                "http://localhost/fr/events/past/",
            },
        )

    @override_settings(
        ROOT_URLCONF="wagtail.test.urls_multilang",
        LANGUAGE_CODE="en",
        WAGTAIL_CONTENT_LANGUAGES=[("en", "English"), ("fr", "French")],
    )
    def test_purge_on_publish_without_i18n_enabled(self):
        with self.captureOnCommitCallbacks(execute=True):
            # It should ignore WAGTAIL_CONTENT_LANGUAGES as WAGTAIL_I18N_ENABLED isn't set
            page = EventIndex.objects.get(url_path="/home/events/")
            page.save_revision().publish()
        self.assertEqual(
            PURGED_URLS,
            {"http://localhost/en/events/", "http://localhost/en/events/past/"},
        )


class TestPurgeBatchClass(TestCase):
    # Tests the .add_*() methods on PurgeBatch. The .purge() method is tested
    # by TestCachePurgingFunctions.test_purge_batch above

    fixtures = ["test.json"]

    def test_add_url(self):
        batch = PurgeBatch()
        batch.add_url("http://localhost/foo")

        self.assertEqual(batch.urls, {"http://localhost/foo"})

    def test_add_urls(self):
        batch = PurgeBatch()
        batch.add_urls(["http://localhost/foo", "http://localhost/bar"])

        self.assertEqual(batch.urls, {"http://localhost/foo", "http://localhost/bar"})

    def test_add_page(self):
        page = EventIndex.objects.get(url_path="/home/events/")

        batch = PurgeBatch()
        batch.add_page(page)

        self.assertEqual(
            batch.urls, {"http://localhost/events/", "http://localhost/events/past/"}
        )

    def test_add_pages(self):
        batch = PurgeBatch()
        batch.add_pages(EventIndex.objects.all())

        self.assertEqual(
            batch.urls, {"http://localhost/events/", "http://localhost/events/past/"}
        )

    def test_multiple_calls(self):
        page = EventIndex.objects.get(url_path="/home/events/")

        batch = PurgeBatch()
        batch.add_page(page)
        batch.add_url("http://localhost/foo")
        batch.purge()

        self.assertEqual(
            batch.urls,
            {
                "http://localhost/events/",
                "http://localhost/events/past/",
                "http://localhost/foo",
            },
        )

    @mock.patch("wagtail.contrib.frontend_cache.backends.cloudflare.requests.delete")
    def test_http_error_on_cloudflare_purge_batch(self, requests_delete_mock):
        backend_settings = {
            "cloudflare": {
                "BACKEND": "wagtail.contrib.frontend_cache.backends.CloudflareBackend",
                "EMAIL": "test@test.com",
                "API_KEY": "this is the api key",
                "ZONEID": "this is a zone id",
            },
        }

        class MockResponse:
            def __init__(self, status_code=200):
                self.status_code = status_code

        http_error = requests.exceptions.HTTPError(
            response=MockResponse(status_code=500)
        )
        requests_delete_mock.side_effect = http_error

        batch = PurgeBatch()
        batch.add_url("http://localhost/events/")

        with self.assertLogs(level="ERROR") as log_output:
            with self.captureOnCommitCallbacks(execute=True):
                batch.purge(backend_settings=backend_settings)

        self.assertIn(
            "Couldn't purge 'http://localhost/events/' from Cloudflare. HTTPError: 500",
            log_output.output[0],
        )
