from django.test import TestCase
from django.test.client import Client
from wagtail.wagtailredirects import models
from wagtail.tests.utils import WagtailTestUtils
from django.core.urlresolvers import reverse


class TestRedirects(TestCase):
    def test_path_normalisation(self):
        # Shortcut to normalise function (to keep things tidy)
        normalise_path = models.Redirect.normalise_path

        # Create a path
        path = normalise_path('/Hello/world.html?foo=Bar&Baz=quux2')

        # Test against equivalant paths
        self.assertEqual(path, normalise_path('/Hello/world.html?foo=Bar&Baz=quux2')) # The exact same URL
        self.assertEqual(path, normalise_path('http://mywebsite.com:8000/Hello/world.html?foo=Bar&Baz=quux2')) # Scheme, hostname and port ignored
        self.assertEqual(path, normalise_path('Hello/world.html?foo=Bar&Baz=quux2')) # Leading slash can be omitted
        self.assertEqual(path, normalise_path('Hello/world.html/?foo=Bar&Baz=quux2')) # Trailing slashes are ignored
        self.assertEqual(path, normalise_path('/Hello/world.html?foo=Bar&Baz=quux2#cool')) # Fragments are ignored
        self.assertEqual(path, normalise_path('/Hello/world.html?Baz=quux2&foo=Bar')) # Order of query string parameters are ignored

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
        redirect = models.Redirect(old_path='/redirectme', redirect_link='/redirectto')
        redirect.save()

        # Navigate to it
        r = c.get('/redirectme/')

        # Check that we were redirected
        self.assertEqual(r.status_code, 301)
        self.assertTrue(r.has_header('Location'))

    def test_temporary_redirect(self):
        # Get a client
        c = Client()

        # Create a redirect
        redirect = models.Redirect(old_path='/redirectme', redirect_link='/redirectto', is_permanent=False)
        redirect.save()

        # Navigate to it
        r = c.get('/redirectme/')

        # Check that we were redirected temporarily
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.has_header('Location'))


class TestRedirectsIndexView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailredirects_index'), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailredirects/index.html')

    def test_search(self):
        response = self.get({'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

    def test_pagination(self):
        pages = ['0', '1', '-1', '9999', 'Not a page']
        for page in pages:
            response = self.get({'p': page})
            self.assertEqual(response.status_code, 200)


class TestRedirectsAddView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailredirects_add_redirect'), params)
 
    def post(self, post_data={}):
        return self.client.post(reverse('wagtailredirects_add_redirect'), post_data)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailredirects/add.html')

    def test_add(self):
        response = self.post({
            'old_path': '/test',
            'is_permanent': 'on',
            'redirect_link': 'http://www.test.com/',
        })

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailredirects_index'))

        # Check that the redirect was created
        redirects = models.Redirect.objects.filter(old_path='/test')
        self.assertEqual(redirects.count(), 1)
        self.assertEqual(redirects.first().redirect_link, 'http://www.test.com/')

    def test_add_validation_error(self):
        response = self.post({
            'old_path': '',
            'is_permanent': 'on',
            'redirect_link': 'http://www.test.com/',
        })

        # Should not redirect to index
        self.assertEqual(response.status_code, 200)


class TestRedirectsEditView(TestCase, WagtailTestUtils):
    def setUp(self):
        # Create a redirect to edit
        self.redirect = models.Redirect(old_path='/test', redirect_link='http://www.test.com/')
        self.redirect.save()

        # Login
        self.login()

    def get(self, params={}, redirect_id=None):
        return self.client.get(reverse('wagtailredirects_edit_redirect', args=(redirect_id or self.redirect.id, )), params)
 
    def post(self, post_data={}, redirect_id=None):
        return self.client.post(reverse('wagtailredirects_edit_redirect', args=(redirect_id or self.redirect.id, )), post_data)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailredirects/edit.html')

    def test_nonexistant_redirect(self):
        self.assertEqual(self.get(redirect_id=100000).status_code, 404)

    def test_edit(self):
        response = self.post({
            'old_path': '/test',
            'is_permanent': 'on',
            'redirect_link': 'http://www.test.com/ive-been-edited',
        })

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailredirects_index'))

        # Check that the redirect was edited
        redirects = models.Redirect.objects.filter(old_path='/test')
        self.assertEqual(redirects.count(), 1)
        self.assertEqual(redirects.first().redirect_link, 'http://www.test.com/ive-been-edited')

    def test_edit_validation_error(self):
        response = self.post({
            'old_path': '',
            'is_permanent': 'on',
            'redirect_link': 'http://www.test.com/ive-been-edited',
        })

        # Should not redirect to index
        self.assertEqual(response.status_code, 200)

class TestRedirectsDeleteView(TestCase, WagtailTestUtils):
    def setUp(self):
        # Create a redirect to edit
        self.redirect = models.Redirect(old_path='/test', redirect_link='http://www.test.com/')
        self.redirect.save()

        # Login
        self.login()

    def get(self, params={}, redirect_id=None):
        return self.client.get(reverse('wagtailredirects_delete_redirect', args=(redirect_id or self.redirect.id, )), params)
 
    def post(self, post_data={}, redirect_id=None):
        return self.client.post(reverse('wagtailredirects_delete_redirect', args=(redirect_id or self.redirect.id, )), post_data)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailredirects/confirm_delete.html')

    def test_nonexistant_redirect(self):
        self.assertEqual(self.get(redirect_id=100000).status_code, 404)

    def test_delete(self):
        response = self.post({
            'hello': 'world'
        })

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailredirects_index'))

        # Check that the redirect was deleted
        redirects = models.Redirect.objects.filter(old_path='/test')
        self.assertEqual(redirects.count(), 0)
