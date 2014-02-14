from django.test import TestCase
from django.test.client import Client
from wagtail.wagtailredirects import models


def get_default_site():
    from wagtail.wagtailcore.models import Site
    return Site.objects.filter(is_default_site=True).first()


def get_default_host():
    return get_default_site().root_url.split('://')[1]


class TestRedirects(TestCase):
    def test_path_normalisation(self):
        # Shortcut to normalise function (to keep things tidy)
        normalise_path = models.Redirect.normalise_path

        # Create a path
        path = normalise_path('/Hello/world.html?foo=Bar&Baz=quux2')

        # Test against equivilant paths
        self.assertEqual(path, normalise_path('/Hello/world.html?foo=Bar&Baz=quux2')) # The exact same URL
        self.assertEqual(path, normalise_path('Hello/world.html?foo=Bar&Baz=quux2')) # Leading slash can be omitted
        self.assertEqual(path, normalise_path('Hello/world.html/?foo=Bar&Baz=quux2')) # Trailing slashes are ignored
        self.assertEqual(path, normalise_path('/Hello/world.html?foo=Bar&Baz=quux2#cool')) # Fragments are ignored
        self.assertEqual(path, normalise_path('/Hello/world.html?Baz=quux2&foo=Bar')) # Order of query string paramters are ignored

        # Test against different paths
        self.assertNotEqual(path, normalise_path('/hello/world.html?foo=Bar&Baz=quux2')) # 'hello' is lowercase
        self.assertNotEqual(path, normalise_path('/Hello/world?foo=Bar&Baz=quux2')) # No '.html'
        self.assertNotEqual(path, normalise_path('/Hello/world.html?foo=bar&Baz=Quux2')) # Query string parameters have wrong case
        self.assertNotEqual(path, normalise_path('/Hello/world.html?foo=Bar&baz=quux2')) # ditto
        self.assertNotEqual(path, normalise_path('/Hello/WORLD.html?foo=Bar&Baz=quux2')) # 'WORLD' is uppercase
        self.assertNotEqual(path, normalise_path('/Hello/world.htm?foo=Bar&Baz=quux2')) # '.htm' is not the same as '.html'

        # Normalise some rubbish to make sure it doesn't crash
        normalise_path('This is not a URL')
        normalise_path('//////hello/world')
        normalise_path('!#@%$*')
        normalise_path('C:\\Program Files (x86)\\Some random program\\file.txt')

    def test_basic_redirect(self):
        # Get a client
        c = Client()

        # Create a redirect
        redirect = models.Redirect(old_path='/redirectme', redirect_link='/redirectto', site=get_default_site())
        redirect.save()

        # Navigate to it
        r = c.get('/redirectme/', HTTP_HOST=get_default_host())

        # Check that we were redirected
        self.assertEqual(r.status_code, 301)
        self.assertTrue(r.has_header('Location'))

    def test_temporary_redirect(self):
        # Get a client
        c = Client()

        # Create a redirect
        redirect = models.Redirect(old_path='/redirectme', redirect_link='/redirectto', site=get_default_site(), is_permanent=False)
        redirect.save()

        # Navigate to it
        r = c.get('/redirectme/', HTTP_HOST=get_default_host())

        # Check that we were redirected temporarily
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.has_header('Location'))