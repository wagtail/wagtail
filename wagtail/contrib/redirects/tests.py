# -*- coding: utf-8 -*-
from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail.contrib.redirects import models
from wagtail.core.models import Page, Site
from wagtail.tests.utils import WagtailTestUtils


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', 'test.example.com', 'other.example.com'])
class TestRedirects(TestCase):
    fixtures = ['test.json']

    def test_path_normalisation(self):
        # Shortcut to normalise function (to keep things tidy)
        normalise_path = models.Redirect.normalise_path

        # Create a path
        path = normalise_path('/Hello/world.html;fizz=three;buzz=five?foo=Bar&Baz=quux2')

        # Test against equivalant paths
        self.assertEqual(path, normalise_path(  # The exact same URL
            '/Hello/world.html;fizz=three;buzz=five?foo=Bar&Baz=quux2'
        ))
        self.assertEqual(path, normalise_path(  # Scheme, hostname and port ignored
            'http://mywebsite.com:8000/Hello/world.html;fizz=three;buzz=five?foo=Bar&Baz=quux2'
        ))
        self.assertEqual(path, normalise_path(  # Leading slash can be omitted
            'Hello/world.html;fizz=three;buzz=five?foo=Bar&Baz=quux2'
        ))
        self.assertEqual(path, normalise_path(  # Trailing slashes are ignored
            'Hello/world.html/;fizz=three;buzz=five?foo=Bar&Baz=quux2'
        ))
        self.assertEqual(path, normalise_path(  # Fragments are ignored
            '/Hello/world.html;fizz=three;buzz=five?foo=Bar&Baz=quux2#cool'
        ))
        self.assertEqual(path, normalise_path(  # Order of query string parameters is ignored
            '/Hello/world.html;fizz=three;buzz=five?Baz=quux2&foo=Bar'
        ))
        self.assertEqual(path, normalise_path(  # Order of parameters is ignored
            '/Hello/world.html;buzz=five;fizz=three?foo=Bar&Baz=quux2'
        ))
        self.assertEqual(path, normalise_path(  # Leading whitespace
            '  /Hello/world.html;fizz=three;buzz=five?foo=Bar&Baz=quux2'
        ))
        self.assertEqual(path, normalise_path(  # Trailing whitespace
            '/Hello/world.html;fizz=three;buzz=five?foo=Bar&Baz=quux2  '
        ))

        # Test against different paths
        self.assertNotEqual(path, normalise_path(  # 'hello' is lowercase
            '/hello/world.html;fizz=three;buzz=five?foo=Bar&Baz=quux2'
        ))
        self.assertNotEqual(path, normalise_path(  # No '.html'
            '/Hello/world;fizz=three;buzz=five?foo=Bar&Baz=quux2'
        ))
        self.assertNotEqual(path, normalise_path(  # Query string parameter value has wrong case
            '/Hello/world.html;fizz=three;buzz=five?foo=bar&Baz=Quux2'
        ))
        self.assertNotEqual(path, normalise_path(  # Query string parameter name has wrong case
            '/Hello/world.html;fizz=three;buzz=five?foo=Bar&baz=quux2'
        ))
        self.assertNotEqual(path, normalise_path(  # Parameter value has wrong case
            '/Hello/world.html;fizz=three;buzz=Five?foo=Bar&Baz=quux2'
        ))
        self.assertNotEqual(path, normalise_path(  # Parameter name has wrong case
            '/Hello/world.html;Fizz=three;buzz=five?foo=Bar&Baz=quux2'
        ))
        self.assertNotEqual(path, normalise_path(  # Missing params
            '/Hello/world.html?foo=Bar&Baz=quux2'
        ))
        self.assertNotEqual(path, normalise_path(  # 'WORLD' is uppercase
            '/Hello/WORLD.html;fizz=three;buzz=five?foo=Bar&Baz=quux2'
        ))
        self.assertNotEqual(path, normalise_path(  # '.htm' is not the same as '.html'
            '/Hello/world.htm;fizz=three;buzz=five?foo=Bar&Baz=quux2'
        ))

        self.assertEqual('/', normalise_path('/'))  # '/' should stay '/'

        # Normalise some rubbish to make sure it doesn't crash
        normalise_path('This is not a URL')
        normalise_path('//////hello/world')
        normalise_path('!#@%$*')
        normalise_path('C:\\Program Files (x86)\\Some random program\\file.txt')

    def test_unicode_path_normalisation(self):
        normalise_path = models.Redirect.normalise_path

        self.assertEqual(
            '/here/tésting-ünicode',  # stays the same
            normalise_path('/here/tésting-ünicode')
        )

        self.assertNotEqual(  # Doesn't remove unicode characters
            '/here/testing-unicode',
            normalise_path('/here/tésting-ünicode')
        )

    def test_basic_redirect(self):
        # Create a redirect
        redirect = models.Redirect(old_path='/redirectme', redirect_link='/redirectto')
        redirect.save()

        # Navigate to it
        response = self.client.get('/redirectme/')

        # Check that we were redirected
        self.assertRedirects(response, '/redirectto', status_code=301, fetch_redirect_response=False)

    def test_temporary_redirect(self):
        # Create a redirect
        redirect = models.Redirect(old_path='/redirectme', redirect_link='/redirectto', is_permanent=False)
        redirect.save()

        # Navigate to it
        response = self.client.get('/redirectme/')

        # Check that we were redirected temporarily
        self.assertRedirects(response, '/redirectto', status_code=302, fetch_redirect_response=False)

    def test_redirect_stripping_query_string(self):
        # Create a redirect which includes a query string
        redirect_with_query_string = models.Redirect(
            old_path='/redirectme?foo=Bar', redirect_link='/with-query-string-only'
        )
        redirect_with_query_string.save()

        # ... and another redirect without the query string
        redirect_without_query_string = models.Redirect(old_path='/redirectme', redirect_link='/without-query-string')
        redirect_without_query_string.save()

        # Navigate to the redirect with the query string
        r_matching_qs = self.client.get('/redirectme/?foo=Bar')
        self.assertRedirects(r_matching_qs, '/with-query-string-only', status_code=301, fetch_redirect_response=False)

        # Navigate to the redirect with a different query string
        # This should strip out the query string and match redirect_without_query_string
        r_no_qs = self.client.get('/redirectme/?utm_source=irrelevant')
        self.assertRedirects(r_no_qs, '/without-query-string', status_code=301, fetch_redirect_response=False)

    def test_redirect_to_page(self):
        christmas_page = Page.objects.get(url_path='/home/events/christmas/')
        models.Redirect.objects.create(old_path='/xmas', redirect_page=christmas_page)

        response = self.client.get('/xmas/', HTTP_HOST='test.example.com')
        # Only one site defined, so redirect should return a local URL
        # (to keep things working if Site records haven't been configured correctly)
        self.assertRedirects(response, '/events/christmas/', status_code=301, fetch_redirect_response=False)

    def test_redirect_from_any_site(self):
        contact_page = Page.objects.get(url_path='/home/contact-us/')
        Site.objects.create(hostname='other.example.com', port=80, root_page=contact_page)

        christmas_page = Page.objects.get(url_path='/home/events/christmas/')
        models.Redirect.objects.create(old_path='/xmas', redirect_page=christmas_page)

        # no site was specified on the redirect, so it should redirect regardless of hostname
        response = self.client.get('/xmas/', HTTP_HOST='localhost')
        self.assertRedirects(response, 'http://localhost/events/christmas/', status_code=301, fetch_redirect_response=False)

        response = self.client.get('/xmas/', HTTP_HOST='other.example.com')
        self.assertRedirects(response, 'http://localhost/events/christmas/', status_code=301, fetch_redirect_response=False)

    def test_redirect_from_specific_site(self):
        contact_page = Page.objects.get(url_path='/home/contact-us/')
        other_site = Site.objects.create(hostname='other.example.com', port=80, root_page=contact_page)

        christmas_page = Page.objects.get(url_path='/home/events/christmas/')
        models.Redirect.objects.create(old_path='/xmas', redirect_page=christmas_page, site=other_site)

        # redirect should only respond when site is other_site
        response = self.client.get('/xmas/', HTTP_HOST='other.example.com')
        self.assertRedirects(response, 'http://localhost/events/christmas/', status_code=301, fetch_redirect_response=False)

        response = self.client.get('/xmas/', HTTP_HOST='localhost')
        self.assertEqual(response.status_code, 404)

    def test_duplicate_redirects_when_match_is_for_generic(self):
        contact_page = Page.objects.get(url_path='/home/contact-us/')
        site = Site.objects.create(hostname='other.example.com', port=80, root_page=contact_page)

        # two redirects, one for any site, one for specific
        models.Redirect.objects.create(old_path='/xmas', redirect_link='/generic')
        models.Redirect.objects.create(site=site, old_path='/xmas', redirect_link='/site-specific')

        response = self.client.get('/xmas/')
        # the redirect which matched was /generic
        self.assertRedirects(response, '/generic', status_code=301, fetch_redirect_response=False)

    def test_duplicate_redirects_with_query_string_when_match_is_for_generic(self):
        contact_page = Page.objects.get(url_path='/home/contact-us/')
        site = Site.objects.create(hostname='other.example.com', port=80, root_page=contact_page)

        # two redirects, one for any site, one for specific, both with query string
        models.Redirect.objects.create(old_path='/xmas?foo=Bar', redirect_link='/generic-with-query-string')
        models.Redirect.objects.create(site=site, old_path='/xmas?foo=Bar', redirect_link='/site-specific-with-query-string')

        # and two redirects, one for any site, one for specific, without query strings
        models.Redirect.objects.create(old_path='/xmas', redirect_link='/generic')
        models.Redirect.objects.create(site=site, old_path='/xmas', redirect_link='/site-specific')

        response = self.client.get('/xmas/?foo=Bar')
        # the redirect which matched was /generic-with-query-string
        self.assertRedirects(response, '/generic-with-query-string', status_code=301, fetch_redirect_response=False)

        # now use a non-matching query string
        response = self.client.get('/xmas/?foo=Baz')
        # the redirect which matched was /generic
        self.assertRedirects(response, '/generic', status_code=301, fetch_redirect_response=False)

    def test_duplicate_redirects_when_match_is_for_specific(self):
        contact_page = Page.objects.get(url_path='/home/contact-us/')
        site = Site.objects.create(hostname='other.example.com', port=80, root_page=contact_page)

        # two redirects, one for any site, one for specific
        models.Redirect.objects.create(old_path='/xmas', redirect_link='/generic')
        models.Redirect.objects.create(site=site, old_path='/xmas', redirect_link='/site-specific')

        response = self.client.get('/xmas/', HTTP_HOST='other.example.com')
        # the redirect which matched was /site-specific
        self.assertRedirects(response, '/site-specific', status_code=301, fetch_redirect_response=False)

    def test_duplicate_redirects_with_query_string_when_match_is_for_specific_with_qs(self):
        contact_page = Page.objects.get(url_path='/home/contact-us/')
        site = Site.objects.create(hostname='other.example.com', port=80, root_page=contact_page)

        # two redirects, one for any site, one for specific, both with query string
        models.Redirect.objects.create(old_path='/xmas?foo=Bar', redirect_link='/generic-with-query-string')
        models.Redirect.objects.create(site=site, old_path='/xmas?foo=Bar', redirect_link='/site-specific-with-query-string')

        # and two redirects, one for any site, one for specific, without query strings
        models.Redirect.objects.create(old_path='/xmas', redirect_link='/generic')
        models.Redirect.objects.create(site=site, old_path='/xmas', redirect_link='/site-specific')

        response = self.client.get('/xmas/?foo=Bar', HTTP_HOST='other.example.com')
        # the redirect which matched was /site-specific-with-query-string
        self.assertRedirects(response, '/site-specific-with-query-string', status_code=301, fetch_redirect_response=False)

        # now use a non-matching query string
        response = self.client.get('/xmas/?foo=Baz', HTTP_HOST='other.example.com')
        # the redirect which matched was /site-specific
        self.assertRedirects(response, '/site-specific', status_code=301, fetch_redirect_response=False)

    def test_duplicate_page_redirects_when_match_is_for_specific(self):
        contact_page = Page.objects.get(url_path='/home/contact-us/')
        site = Site.objects.create(hostname='other.example.com', port=80, root_page=contact_page)
        christmas_page = Page.objects.get(url_path='/home/events/christmas/')

        # two redirects, one for any site, one for specific
        models.Redirect.objects.create(old_path='/xmas', redirect_page=contact_page)
        models.Redirect.objects.create(site=site, old_path='/xmas', redirect_page=christmas_page)

        # request for specific site gets the christmas_page redirect, not accessible from other.example.com
        response = self.client.get('/xmas/', HTTP_HOST='other.example.com')
        self.assertRedirects(response, 'http://localhost/events/christmas/', status_code=301, fetch_redirect_response=False)

    def test_redirect_with_unicode_in_url(self):
        redirect = models.Redirect(old_path='/tésting-ünicode', redirect_link='/redirectto')
        redirect.save()

        # Navigate to it
        response = self.client.get('/tésting-ünicode/')

        self.assertRedirects(response, '/redirectto', status_code=301, fetch_redirect_response=False)

    def test_redirect_with_encoded_url(self):
        redirect = models.Redirect(old_path='/t%C3%A9sting-%C3%BCnicode', redirect_link='/redirectto')
        redirect.save()

        # Navigate to it
        response = self.client.get('/t%C3%A9sting-%C3%BCnicode/')

        self.assertRedirects(response, '/redirectto', status_code=301, fetch_redirect_response=False)


class TestRedirectsIndexView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailredirects:index'), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailredirects/index.html')

    def test_search(self):
        response = self.get({'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

    def test_search_results(self):
        models.Redirect.objects.create(old_path="/aaargh", redirect_link="http://torchbox.com/")
        models.Redirect.objects.create(old_path="/torchbox", redirect_link="http://aaargh.com/")
        response = self.get({'q': "aaargh"})
        self.assertEqual(len(response.context['redirects']), 2)

    def test_pagination(self):
        pages = ['0', '1', '-1', '9999', 'Not a page']
        for page in pages:
            response = self.get({'p': page})
            self.assertEqual(response.status_code, 200)

    def test_listing_order(self):
        for i in range(0, 10):
            models.Redirect.objects.create(old_path="/redirect%d" % i, redirect_link="http://torchbox.com/")

        models.Redirect.objects.create(old_path="/aaargh", redirect_link="http://torchbox.com/")

        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['redirects'][0].old_path, "/aaargh")


class TestRedirectsAddView(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailredirects:add'), params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailredirects:add'), post_data)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailredirects/add.html')

    def test_add(self):
        response = self.post({
            'old_path': '/test',
            'site': '',
            'is_permanent': 'on',
            'redirect_link': 'http://www.test.com/',
        })

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailredirects:index'))

        # Check that the redirect was created
        redirects = models.Redirect.objects.filter(old_path='/test')
        self.assertEqual(redirects.count(), 1)
        self.assertEqual(redirects.first().redirect_link, 'http://www.test.com/')
        self.assertEqual(redirects.first().site, None)

    def test_add_with_site(self):
        localhost = Site.objects.get(hostname='localhost')
        response = self.post({
            'old_path': '/test',
            'site': localhost.id,
            'is_permanent': 'on',
            'redirect_link': 'http://www.test.com/',
        })

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailredirects:index'))

        # Check that the redirect was created
        redirects = models.Redirect.objects.filter(old_path='/test')
        self.assertEqual(redirects.count(), 1)
        self.assertEqual(redirects.first().redirect_link, 'http://www.test.com/')
        self.assertEqual(redirects.first().site, localhost)

    def test_add_validation_error(self):
        response = self.post({
            'old_path': '',
            'site': '',
            'is_permanent': 'on',
            'redirect_link': 'http://www.test.com/',
        })

        # Should not redirect to index
        self.assertEqual(response.status_code, 200)

    def test_cannot_add_duplicate_with_no_site(self):
        models.Redirect.objects.create(old_path='/test', site=None, redirect_link='http://elsewhere.com/')
        response = self.post({
            'old_path': '/test',
            'site': '',
            'is_permanent': 'on',
            'redirect_link': 'http://www.test.com/',
        })

        # Should not redirect to index
        self.assertEqual(response.status_code, 200)

    def test_cannot_add_duplicate_on_same_site(self):
        localhost = Site.objects.get(hostname='localhost')
        models.Redirect.objects.create(old_path='/test', site=localhost, redirect_link='http://elsewhere.com/')
        response = self.post({
            'old_path': '/test',
            'site': localhost.pk,
            'is_permanent': 'on',
            'redirect_link': 'http://www.test.com/',
        })

        # Should not redirect to index
        self.assertEqual(response.status_code, 200)

    def test_can_reuse_path_on_other_site(self):
        localhost = Site.objects.get(hostname='localhost')
        contact_page = Page.objects.get(url_path='/home/contact-us/')
        other_site = Site.objects.create(hostname='other.example.com', port=80, root_page=contact_page)

        models.Redirect.objects.create(old_path='/test', site=localhost, redirect_link='http://elsewhere.com/')
        response = self.post({
            'old_path': '/test',
            'site': other_site.pk,
            'is_permanent': 'on',
            'redirect_link': 'http://www.test.com/',
        })

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailredirects:index'))

        # Check that the redirect was created
        redirects = models.Redirect.objects.filter(redirect_link='http://www.test.com/')
        self.assertEqual(redirects.count(), 1)


class TestRedirectsEditView(TestCase, WagtailTestUtils):
    def setUp(self):
        # Create a redirect to edit
        self.redirect = models.Redirect(old_path='/test', redirect_link='http://www.test.com/')
        self.redirect.save()

        # Login
        self.login()

    def get(self, params={}, redirect_id=None):
        return self.client.get(reverse('wagtailredirects:edit', args=(redirect_id or self.redirect.id, )), params)

    def post(self, post_data={}, redirect_id=None):
        return self.client.post(reverse('wagtailredirects:edit', args=(redirect_id or self.redirect.id, )), post_data)

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
            'site': '',
            'redirect_link': 'http://www.test.com/ive-been-edited',
        })

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailredirects:index'))

        # Check that the redirect was edited
        redirects = models.Redirect.objects.filter(old_path='/test')
        self.assertEqual(redirects.count(), 1)
        self.assertEqual(redirects.first().redirect_link, 'http://www.test.com/ive-been-edited')
        self.assertEqual(redirects.first().site, None)

    def test_edit_with_site(self):
        localhost = Site.objects.get(hostname='localhost')

        response = self.post({
            'old_path': '/test',
            'is_permanent': 'on',
            'site': localhost.id,
            'redirect_link': 'http://www.test.com/ive-been-edited',
        })

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailredirects:index'))

        # Check that the redirect was edited
        redirects = models.Redirect.objects.filter(old_path='/test')
        self.assertEqual(redirects.count(), 1)
        self.assertEqual(redirects.first().redirect_link, 'http://www.test.com/ive-been-edited')
        self.assertEqual(redirects.first().site, localhost)

    def test_edit_validation_error(self):
        response = self.post({
            'old_path': '',
            'is_permanent': 'on',
            'site': '',
            'redirect_link': 'http://www.test.com/ive-been-edited',
        })

        # Should not redirect to index
        self.assertEqual(response.status_code, 200)

    def test_edit_duplicate(self):
        models.Redirect.objects.create(old_path='/othertest', site=None, redirect_link='http://elsewhere.com/')
        response = self.post({
            'old_path': '/othertest',
            'is_permanent': 'on',
            'site': '',
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
        return self.client.get(reverse('wagtailredirects:delete', args=(redirect_id or self.redirect.id, )), params)

    def post(self, redirect_id=None):
        return self.client.post(reverse(
            'wagtailredirects:delete', args=(redirect_id or self.redirect.id, )
        ))

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailredirects/confirm_delete.html')

    def test_nonexistant_redirect(self):
        self.assertEqual(self.get(redirect_id=100000).status_code, 404)

    def test_delete(self):
        response = self.post()

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailredirects:index'))

        # Check that the redirect was deleted
        redirects = models.Redirect.objects.filter(old_path='/test')
        self.assertEqual(redirects.count(), 0)
