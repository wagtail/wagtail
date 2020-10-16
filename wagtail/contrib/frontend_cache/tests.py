from unittest import mock
from urllib.error import HTTPError, URLError

import requests

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.test.utils import override_settings

from wagtail.contrib.frontend_cache.backends import (
    BaseBackend, CloudflareBackend, CloudfrontBackend, HTTPBackend)
from wagtail.contrib.frontend_cache.utils import get_backends
from wagtail.core.models import Page
from wagtail.tests.testapp.models import EventIndex

from .utils import (
    PurgeBatch, purge_page_from_cache, purge_pages_from_cache, purge_url_from_cache,
    purge_urls_from_cache)


class TestBackendConfiguration(TestCase):
    def test_default(self):
        backends = get_backends()

        self.assertEqual(len(backends), 0)

    def test_varnish(self):
        backends = get_backends(backend_settings={
            'varnish': {
                'BACKEND': 'wagtail.contrib.frontend_cache.backends.HTTPBackend',
                'LOCATION': 'http://localhost:8000',
            },
        })

        self.assertEqual(set(backends.keys()), set(['varnish']))
        self.assertIsInstance(backends['varnish'], HTTPBackend)

        self.assertEqual(backends['varnish'].cache_scheme, 'http')
        self.assertEqual(backends['varnish'].cache_netloc, 'localhost:8000')

    def test_cloudflare(self):
        backends = get_backends(backend_settings={
            'cloudflare': {
                'BACKEND': 'wagtail.contrib.frontend_cache.backends.CloudflareBackend',
                'EMAIL': 'test@test.com',
                'API_KEY': 'this is the api key',
                'ZONEID': 'this is a zone id',
                'BEARER_TOKEN': 'this is a bearer token'
            },
        })

        self.assertEqual(set(backends.keys()), set(['cloudflare']))
        self.assertIsInstance(backends['cloudflare'], CloudflareBackend)

        self.assertEqual(backends['cloudflare'].cloudflare_email, 'test@test.com')
        self.assertEqual(backends['cloudflare'].cloudflare_api_key, 'this is the api key')
        self.assertEqual(backends['cloudflare'].cloudflare_token, 'this is a bearer token')

    def test_cloudfront(self):
        backends = get_backends(backend_settings={
            'cloudfront': {
                'BACKEND': 'wagtail.contrib.frontend_cache.backends.CloudfrontBackend',
                'DISTRIBUTION_ID': 'frontend',
            },
        })

        self.assertEqual(set(backends.keys()), set(['cloudfront']))
        self.assertIsInstance(backends['cloudfront'], CloudfrontBackend)

        self.assertEqual(backends['cloudfront'].cloudfront_distribution_id, 'frontend')

    def test_http(self):
        """Test that `HTTPBackend.purge` works when urlopen succeeds"""
        self._test_http_with_side_effect(urlopen_side_effect=None)

    def test_http_httperror(self):
        """Test that `HTTPBackend.purge` can handle `HTTPError`"""
        http_error = HTTPError(
            url='http://localhost:8000/home/events/christmas/',
            code=500,
            msg='Internal Server Error',
            hdrs={},
            fp=None
        )
        with self.assertLogs(level='ERROR') as log_output:
            self._test_http_with_side_effect(urlopen_side_effect=http_error)

        self.assertIn(
            "Couldn't purge 'http://www.wagtail.io/home/events/christmas/' from HTTP cache. HTTPError: 500 Internal Server Error",
            log_output.output[0]
        )

    def test_http_urlerror(self):
        """Test that `HTTPBackend.purge` can handle `URLError`"""
        url_error = URLError(reason='just for tests')
        with self.assertLogs(level='ERROR') as log_output:
            self._test_http_with_side_effect(urlopen_side_effect=url_error)
        self.assertIn(
            "Couldn't purge 'http://www.wagtail.io/home/events/christmas/' from HTTP cache. URLError: just for tests",
            log_output.output[0]
        )

    @mock.patch('wagtail.contrib.frontend_cache.backends.urlopen')
    def _test_http_with_side_effect(self, urlopen_mock, urlopen_side_effect):
        # given a backends configuration with one HTTP backend
        backends = get_backends(backend_settings={
            'varnish': {
                'BACKEND': 'wagtail.contrib.frontend_cache.backends.HTTPBackend',
                'LOCATION': 'http://localhost:8000',
            },
        })
        self.assertEqual(set(backends.keys()), set(['varnish']))
        self.assertIsInstance(backends['varnish'], HTTPBackend)
        # and mocked urlopen that may or may not raise network-related exception
        urlopen_mock.side_effect = urlopen_side_effect

        # when making a purge request
        backends.get('varnish').purge('http://www.wagtail.io/home/events/christmas/')

        # then no exception is raised
        # and mocked urlopen is called with a proper purge request
        self.assertEqual(urlopen_mock.call_count, 1)
        (purge_request,), _call_kwargs = urlopen_mock.call_args
        self.assertEqual(purge_request.full_url, 'http://localhost:8000/home/events/christmas/')

    def test_cloudfront_validate_distribution_id(self):
        with self.assertRaises(ImproperlyConfigured):
            get_backends(backend_settings={
                'cloudfront': {
                    'BACKEND': 'wagtail.contrib.frontend_cache.backends.CloudfrontBackend',
                },
            })

    @mock.patch('wagtail.contrib.frontend_cache.backends.CloudfrontBackend._create_invalidation')
    def test_cloudfront_distribution_id_mapping(self, _create_invalidation):
        backends = get_backends(backend_settings={
            'cloudfront': {
                'BACKEND': 'wagtail.contrib.frontend_cache.backends.CloudfrontBackend',
                'DISTRIBUTION_ID': {
                    'www.wagtail.io': 'frontend',
                }
            },
        })
        backends.get('cloudfront').purge('http://www.wagtail.io/home/events/christmas/')
        backends.get('cloudfront').purge('http://torchbox.com/blog/')

        _create_invalidation.assert_called_once_with('frontend', ['/home/events/christmas/'])

    def test_multiple(self):
        backends = get_backends(backend_settings={
            'varnish': {
                'BACKEND': 'wagtail.contrib.frontend_cache.backends.HTTPBackend',
                'LOCATION': 'http://localhost:8000/',
            },
            'cloudflare': {
                'BACKEND': 'wagtail.contrib.frontend_cache.backends.CloudflareBackend',
                'EMAIL': 'test@test.com',
                'API_KEY': 'this is the api key',
                'ZONEID': 'this is a zone id',
            }
        })

        self.assertEqual(set(backends.keys()), set(['varnish', 'cloudflare']))

    def test_filter(self):
        backends = get_backends(backend_settings={
            'varnish': {
                'BACKEND': 'wagtail.contrib.frontend_cache.backends.HTTPBackend',
                'LOCATION': 'http://localhost:8000/',
            },
            'cloudflare': {
                'BACKEND': 'wagtail.contrib.frontend_cache.backends.CloudflareBackend',
                'EMAIL': 'test@test.com',
                'API_KEY': 'this is the api key',
                'ZONEID': 'this is a zone id',
            }
        }, backends=['cloudflare'])

        self.assertEqual(set(backends.keys()), set(['cloudflare']))

    @override_settings(WAGTAILFRONTENDCACHE_LOCATION='http://localhost:8000')
    def test_backwards_compatibility(self):
        backends = get_backends()

        self.assertEqual(set(backends.keys()), set(['default']))
        self.assertIsInstance(backends['default'], HTTPBackend)
        self.assertEqual(backends['default'].cache_scheme, 'http')
        self.assertEqual(backends['default'].cache_netloc, 'localhost:8000')


PURGED_URLS = []


class MockBackend(BaseBackend):
    def __init__(self, config):
        pass

    def purge(self, url):
        PURGED_URLS.append(url)


class MockCloudflareBackend(CloudflareBackend):
    def __init__(self, config):
        pass

    def _purge_urls(self, urls):
        if len(urls) > self.CHUNK_SIZE:
            raise Exception("Cloudflare backend is not chunking requests as expected")

        PURGED_URLS.extend(urls)


@override_settings(WAGTAILFRONTENDCACHE={
    'varnish': {
        'BACKEND': 'wagtail.contrib.frontend_cache.tests.MockBackend',
    },
})
class TestCachePurgingFunctions(TestCase):

    fixtures = ['test.json']

    def setUp(self):
        # Reset PURGED_URLS to an empty list
        PURGED_URLS[:] = []

    def test_purge_url_from_cache(self):
        purge_url_from_cache('http://localhost/foo')
        self.assertEqual(PURGED_URLS, ['http://localhost/foo'])

    def test_purge_urls_from_cache(self):
        purge_urls_from_cache(['http://localhost/foo', 'http://localhost/bar'])
        self.assertEqual(PURGED_URLS, ['http://localhost/foo', 'http://localhost/bar'])

    def test_purge_page_from_cache(self):
        page = EventIndex.objects.get(url_path='/home/events/')
        purge_page_from_cache(page)
        self.assertEqual(PURGED_URLS, ['http://localhost/events/', 'http://localhost/events/past/'])

    def test_purge_pages_from_cache(self):
        purge_pages_from_cache(EventIndex.objects.all())
        self.assertEqual(PURGED_URLS, ['http://localhost/events/', 'http://localhost/events/past/'])

    def test_purge_batch(self):
        batch = PurgeBatch()
        page = EventIndex.objects.get(url_path='/home/events/')
        batch.add_page(page)
        batch.add_url('http://localhost/foo')
        batch.purge()

        self.assertEqual(PURGED_URLS, ['http://localhost/events/', 'http://localhost/events/past/', 'http://localhost/foo'])


@override_settings(WAGTAILFRONTENDCACHE={
    'cloudflare': {
        'BACKEND': 'wagtail.contrib.frontend_cache.tests.MockCloudflareBackend',
    },
})
class TestCloudflareCachePurgingFunctions(TestCase):
    def setUp(self):
        # Reset PURGED_URLS to an empty list
        PURGED_URLS[:] = []

    def test_cloudflare_purge_batch_chunked(self):
        batch = PurgeBatch()
        urls = ['https://localhost/foo{}'.format(i) for i in range(1, 65)]
        batch.add_urls(urls)
        batch.purge()

        self.assertCountEqual(PURGED_URLS, urls)


@override_settings(WAGTAILFRONTENDCACHE={
    'varnish': {
        'BACKEND': 'wagtail.contrib.frontend_cache.tests.MockBackend',
    },
})
class TestCachePurgingSignals(TestCase):

    fixtures = ['test.json']

    def setUp(self):
        # Reset PURGED_URLS to an empty list
        PURGED_URLS[:] = []

    def test_purge_on_publish(self):
        page = EventIndex.objects.get(url_path='/home/events/')
        page.save_revision().publish()
        self.assertEqual(PURGED_URLS, ['http://localhost/events/', 'http://localhost/events/past/'])

    def test_purge_on_unpublish(self):
        page = EventIndex.objects.get(url_path='/home/events/')
        page.unpublish()
        self.assertEqual(PURGED_URLS, ['http://localhost/events/', 'http://localhost/events/past/'])

    def test_purge_with_unroutable_page(self):
        root = Page.objects.get(url_path='/')
        page = EventIndex(title='new top-level page')
        root.add_child(instance=page)
        page.save_revision().publish()
        self.assertEqual(PURGED_URLS, [])

    @override_settings(ROOT_URLCONF='wagtail.tests.urls_multilang',
                       LANGUAGE_CODE='en',
                       WAGTAILFRONTENDCACHE_LANGUAGES=['en', 'fr', 'pt-br'])
    def test_purge_on_publish_in_multilang_env(self):
        PURGED_URLS[:] = []  # reset PURGED_URLS to the empty list
        page = EventIndex.objects.get(url_path='/home/events/')
        page.save_revision().publish()

        self.assertEqual(PURGED_URLS, [
            'http://localhost/en/events/',
            'http://localhost/en/events/past/',
            'http://localhost/fr/events/',
            'http://localhost/fr/events/past/',
            'http://localhost/pt-br/events/',
            'http://localhost/pt-br/events/past/',
        ])

    @override_settings(ROOT_URLCONF='wagtail.tests.urls_multilang',
                       LANGUAGE_CODE='en',
                       WAGTAIL_I18N_ENABLED=True,
                       WAGTAIL_CONTENT_LANGUAGES=[('en', 'English'), ('fr', 'French')])
    def test_purge_on_publish_with_i18n_enabled(self):
        PURGED_URLS[:] = []  # reset PURGED_URLS to the empty list
        page = EventIndex.objects.get(url_path='/home/events/')
        page.save_revision().publish()

        self.assertEqual(PURGED_URLS, [
            'http://localhost/en/events/',
            'http://localhost/en/events/past/',
            'http://localhost/fr/events/',
            'http://localhost/fr/events/past/',
        ])

    @override_settings(ROOT_URLCONF='wagtail.tests.urls_multilang',
                       LANGUAGE_CODE='en',
                       WAGTAIL_CONTENT_LANGUAGES=[('en', 'English'), ('fr', 'French')])
    def test_purge_on_publish_without_i18n_enabled(self):
        # It should ignore WAGTAIL_CONTENT_LANGUAGES as WAGTAIL_I18N_ENABLED isn't set
        PURGED_URLS[:] = []  # reset PURGED_URLS to the empty list
        page = EventIndex.objects.get(url_path='/home/events/')
        page.save_revision().publish()
        self.assertEqual(PURGED_URLS, ['http://localhost/en/events/', 'http://localhost/en/events/past/'])


class TestPurgeBatchClass(TestCase):
    # Tests the .add_*() methods on PurgeBatch. The .purge() method is tested
    # by TestCachePurgingFunctions.test_purge_batch above

    fixtures = ['test.json']

    def test_add_url(self):
        batch = PurgeBatch()
        batch.add_url('http://localhost/foo')

        self.assertEqual(batch.urls, ['http://localhost/foo'])

    def test_add_urls(self):
        batch = PurgeBatch()
        batch.add_urls(['http://localhost/foo', 'http://localhost/bar'])

        self.assertEqual(batch.urls, ['http://localhost/foo', 'http://localhost/bar'])

    def test_add_page(self):
        page = EventIndex.objects.get(url_path='/home/events/')

        batch = PurgeBatch()
        batch.add_page(page)

        self.assertEqual(batch.urls, ['http://localhost/events/', 'http://localhost/events/past/'])

    def test_add_pages(self):
        batch = PurgeBatch()
        batch.add_pages(EventIndex.objects.all())

        self.assertEqual(batch.urls, ['http://localhost/events/', 'http://localhost/events/past/'])

    def test_multiple_calls(self):
        page = EventIndex.objects.get(url_path='/home/events/')

        batch = PurgeBatch()
        batch.add_page(page)
        batch.add_url('http://localhost/foo')
        batch.purge()

        self.assertEqual(batch.urls, ['http://localhost/events/', 'http://localhost/events/past/', 'http://localhost/foo'])

    @mock.patch('wagtail.contrib.frontend_cache.backends.requests.delete')
    def test_http_error_on_cloudflare_purge_batch(self, requests_delete_mock):
        backend_settings = {
            'cloudflare': {
                'BACKEND': 'wagtail.contrib.frontend_cache.backends.CloudflareBackend',
                'EMAIL': 'test@test.com',
                'API_KEY': 'this is the api key',
                'ZONEID': 'this is a zone id',
            },
        }

        class MockResponse:
            def __init__(self, status_code=200):
                self.status_code = status_code

        http_error = requests.exceptions.HTTPError(response=MockResponse(status_code=500))
        requests_delete_mock.side_effect = http_error

        page = EventIndex.objects.get(url_path='/home/events/')

        batch = PurgeBatch()
        batch.add_page(page)

        with self.assertLogs(level='ERROR') as log_output:
            batch.purge(backend_settings=backend_settings)

        self.assertIn(
            "Couldn't purge 'http://localhost/events/' from Cloudflare. HTTPError: 500",
            log_output.output[0]
        )
