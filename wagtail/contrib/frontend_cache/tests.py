import mock
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
                'TOKEN': 'this is the token',
                'ZONEID': 'this is a zone id',
            },
        })

        self.assertEqual(set(backends.keys()), set(['cloudflare']))
        self.assertIsInstance(backends['cloudflare'], CloudflareBackend)

        self.assertEqual(backends['cloudflare'].cloudflare_email, 'test@test.com')
        self.assertEqual(backends['cloudflare'].cloudflare_token, 'this is the token')

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
                'TOKEN': 'this is the token',
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
                'TOKEN': 'this is the token',
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
                       WAGTAILFRONTENDCACHE_LANGUAGES=['en'])
    def test_purge_on_publish_in_multilang_env(self):
        from django.conf import settings
        PURGED_URLS[:] = []  # reset PURGED_URLS to the empty list
        page = EventIndex.objects.get(url_path='/home/events/')
        page.save_revision().publish()
        self.assertEqual(len(PURGED_URLS), len(settings.WAGTAILFRONTENDCACHE_LANGUAGES) * 2)
        for isocode, description in settings.WAGTAILFRONTENDCACHE_LANGUAGES:
            self.assertIn('http://localhost/%s/events/' % isocode, PURGED_URLS)


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
