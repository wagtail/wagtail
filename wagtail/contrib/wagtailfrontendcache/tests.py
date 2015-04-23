import django
from django.test import TestCase
from django.test.utils import override_settings

from wagtail.wagtailcore.models import Page
from wagtail.tests.models import EventIndex

from wagtail.contrib.wagtailfrontendcache.utils import get_backends
from wagtail.contrib.wagtailfrontendcache.backends import HTTPBackend, CloudflareBackend, BaseBackend


if django.VERSION < (1, 7):
    from wagtail.contrib.wagtailfrontendcache.signal_handlers import register_signal_handlers
    register_signal_handlers()


class TestBackendConfiguration(TestCase):
    def test_default(self):
        backends = get_backends()

        self.assertEqual(len(backends), 0)

    def test_varnish(self):
        backends = get_backends(backend_settings={
            'varnish': {
                'BACKEND': 'wagtail.contrib.wagtailfrontendcache.backends.HTTPBackend',
                'LOCATION': 'http://localhost:8000',
            },
        })

        self.assertEqual(set(backends.keys()), set(['varnish']))
        self.assertIsInstance(backends['varnish'], HTTPBackend)

        self.assertEqual(backends['varnish'].cache_location, 'http://localhost:8000')

    def test_cloudflare(self):
        backends = get_backends(backend_settings={
            'cloudflare': {
                'BACKEND': 'wagtail.contrib.wagtailfrontendcache.backends.CloudflareBackend',
                'EMAIL': 'test@test.com',
                'TOKEN': 'this is the token',
            },
        })

        self.assertEqual(set(backends.keys()), set(['cloudflare']))
        self.assertIsInstance(backends['cloudflare'], CloudflareBackend)

        self.assertEqual(backends['cloudflare'].cloudflare_email, 'test@test.com')
        self.assertEqual(backends['cloudflare'].cloudflare_token, 'this is the token')

    def test_multiple(self):
        backends = get_backends(backend_settings={
            'varnish': {
                'BACKEND': 'wagtail.contrib.wagtailfrontendcache.backends.HTTPBackend',
                'LOCATION': 'http://localhost:8000/',
            },
            'cloudflare': {
                'BACKEND': 'wagtail.contrib.wagtailfrontendcache.backends.CloudflareBackend',
                'EMAIL': 'test@test.com',
                'TOKEN': 'this is the token',
            }
        })

        self.assertEqual(set(backends.keys()), set(['varnish', 'cloudflare']))

    def test_filter(self):
        backends = get_backends(backend_settings={
            'varnish': {
                'BACKEND': 'wagtail.contrib.wagtailfrontendcache.backends.HTTPBackend',
                'LOCATION': 'http://localhost:8000/',
            },
            'cloudflare': {
                'BACKEND': 'wagtail.contrib.wagtailfrontendcache.backends.CloudflareBackend',
                'EMAIL': 'test@test.com',
                'TOKEN': 'this is the token',
            }
        }, backends=['cloudflare'])

        self.assertEqual(set(backends.keys()), set(['cloudflare']))

    @override_settings(WAGTAILFRONTENDCACHE_LOCATION='http://localhost:8000')
    def test_backwards_compatibility(self):
        backends = get_backends()

        self.assertEqual(set(backends.keys()), set(['default']))
        self.assertIsInstance(backends['default'], HTTPBackend)
        self.assertEqual(backends['default'].cache_location, 'http://localhost:8000')


PURGED_URLS = []


class MockBackend(BaseBackend):
    def __init__(self, config):
        pass

    def purge(self, url):
        PURGED_URLS.append(url)


@override_settings(WAGTAILFRONTENDCACHE={
    'varnish': {
        'BACKEND': 'wagtail.contrib.wagtailfrontendcache.tests.MockBackend',
    },
})
class TestCachePurging(TestCase):

    fixtures = ['test.json']

    def test_purge_on_publish(self):
        PURGED_URLS[:] = []  # reset PURGED_URLS to the empty list
        page = EventIndex.objects.get(url_path='/home/events/')
        page.save_revision().publish()
        self.assertEqual(PURGED_URLS, ['http://localhost/events/'])

    def test_purge_on_unpublish(self):
        PURGED_URLS[:] = []  # reset PURGED_URLS to the empty list
        page = EventIndex.objects.get(url_path='/home/events/')
        page.unpublish()
        self.assertEqual(PURGED_URLS, ['http://localhost/events/'])

    def test_purge_with_unroutable_page(self):
        PURGED_URLS[:] = []  # reset PURGED_URLS to the empty list
        root = Page.objects.get(url_path='/')
        page = EventIndex(title='new top-level page', slug='new-top-level-page')
        root.add_child(instance=page)
        page.save_revision().publish()
        self.assertEqual(PURGED_URLS, [])
