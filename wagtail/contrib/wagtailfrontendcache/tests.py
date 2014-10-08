from django.test import TestCase, override_settings

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

        self.assertEqual(len(backends), 1)
        self.assertIsInstance(backends[0], HTTPBackend)

        self.assertEqual(backends[0].cache_location, 'http://localhost:8000')

    def test_cloudflare(self):
        backends = get_backends(backend_settings={
            'cloudflare': {
                'BACKEND': 'wagtail.contrib.wagtailfrontendcache.backends.CloudflareBackend',
                'EMAIL': 'test@test.com',
                'TOKEN': 'this is the token',
            },
        })

        self.assertEqual(len(backends), 1)
        self.assertIsInstance(backends[0], CloudflareBackend)

        self.assertEqual(backends[0].cloudflare_email, 'test@test.com')
        self.assertEqual(backends[0].cloudflare_token, 'this is the token')

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

        self.assertEqual(len(backends), 2)

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

        self.assertEqual(len(backends), 1)
        self.assertIsInstance(backends[0], CloudflareBackend)

    @override_settings(WAGTAILFRONTENDCACHE_LOCATION='http://localhost:8000')
    def test_backwards_compatibility(self):
        backends = get_backends()

        self.assertEqual(len(backends), 1)
        self.assertIsInstance(backends[0], HTTPBackend)
        self.assertEqual(backends[0].cache_location, 'http://localhost:8000')
