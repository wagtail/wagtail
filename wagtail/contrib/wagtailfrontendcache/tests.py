from django.test import TestCase
from django.test.utils import override_settings

from wagtail.contrib.wagtailfrontendcache.utils import get_backends
from wagtail.contrib.wagtailfrontendcache.backends import HTTPBackend, CloudflareBackend


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
