from wagtail.wagtailcore.models import Site
from wagtail.wagtailsearch import models
from django.contrib.auth.models import User
from django.test import TestCase
import unittest


class ViewTestCase(TestCase):
    def get_host(self):
        return Site.objects.filter(is_default_site=True).first().root_url.split('://')[1]

    def login(self):
        # Create a user
        User.objects.create_superuser(username='test', email='test@email.com', password='password')

        # Login
        login = self.client.login(username='test', password='password')

        # Skip if not logged in
        if not login:
            raise unittest.SkipTest("Login failure")

    def get(self, *args, **kwargs):
        # Add HTTP_HOST to kwargs
        kwargs['HTTP_HOST'] = self.get_host()

        # Call client
        return self.client.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        # Add HTTP_HOST to kwargs
        kwargs['HTTP_HOST'] = self.get_host()

        # Call client
        return self.client.post(*args, **kwargs)


class TestFrontendViews(ViewTestCase):
    def test_search(self):
        # Get response
        response = self.get('/search/?q=Hello')

        # Check status code
        self.assertEqual(response.status_code, 200)

    def test_search_noquery(self):
        # Get response
        response = self.get('/search/')

        # Check status code
        self.assertEqual(response.status_code, 200)

    def test_suggest(self):
        # Get response
        response = self.get('/search/suggest/?q=Hello')

        # Check status code
        self.assertEqual(response.status_code, 200)

    def test_suggest_noquery(self):
        # Get response
        response = self.get('/search/suggest/')

        # Check status code
        self.assertEqual(response.status_code, 200)


class TestEditorsPicksViews(ViewTestCase):
    def setUp(self):
        # Login
        self.login()

        # Create a test editors pick
        self.query = models.Query.get("Hello world!")
        self.query.editors_picks.create(page_id=1)

    def test_index(self):
        response = self.get('/admin/search/editorspicks/')

        # Check status code
        self.assertEqual(response.status_code, 200)

    def test_index_search(self):
        response = self.get('/admin/search/editorspicks/?q=Hello')

        # Check status code
        self.assertEqual(response.status_code, 200)

    def test_add(self):
        response = self.get('/admin/search/editorspicks/add/')

        # Check status code
        self.assertEqual(response.status_code, 200)

    def test_edit(self):
        response = self.get('/admin/search/editorspicks/%d/' % self.query.id)

        # Check status code
        self.assertEqual(response.status_code, 200)

    def test_edit_notexists(self):
        response = self.get('/admin/search/editorspicks/12313/')

        # Check status code
        self.assertEqual(response.status_code, 404)

    def test_delete(self):
        response = self.get('/admin/search/editorspicks/%d/delete/' % self.query.id)

        # Check status code
        self.assertEqual(response.status_code, 200)

    def test_delete_notexists(self):
        response = self.get('/admin/search/editorspicks/12313/delete/')

        # Check status code
        self.assertEqual(response.status_code, 404)


class TestQueriesViews(ViewTestCase):
    def setUp(self):
        # Login
        self.login()

    def test_chooser(self):
        response = self.get('/admin/search/queries/chooser/')

        # Check status code
        self.assertEqual(response.status_code, 200)