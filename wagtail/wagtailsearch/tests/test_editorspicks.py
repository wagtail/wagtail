from django.test import TestCase
from .utils import get_default_host, login
from wagtail.wagtailsearch import models


class TestEditorsPicks(TestCase):
    pass


class TestEditorsPicksIndexView(TestCase):
    def setUp(self):
        login(self.client)

    def get(self, params={}):
        return self.client.get('/admin/search/editorspicks/', params, HTTP_HOST=get_default_host())

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_search_status_code(self):
        self.assertEqual(self.get({'q': "Hello"}).status_code, 200)

    def test_search_template_context(self):
        self.assertEqual(self.get({'q': "Hello"}).context['search_query'], "Hello")

    def test_page_status_code(self):
        self.assertEqual(self.get({'p': '1'}).status_code, 200)


class TestEditorsPicksAddView(TestCase):
    def setUp(self):
        login(self.client)

    def get(self, params={}):
        return self.client.get('/admin/search/editorspicks/add/', params, HTTP_HOST=get_default_host())

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)


class TestEditorsPicksEditView(TestCase):
    def setUp(self):
        login(self.client)

        # Create an editors pick to edit
        self.query = models.Query.get("Hello")
        self.query.editors_picks.create(page_id=1, description="Root page")

    def get(self, params={}):
        return self.client.get('/admin/search/editorspicks/' + str(self.query.id) + '/', params, HTTP_HOST=get_default_host())

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)


class TestEditorsPicksDeleteView(TestCase):
    def setUp(self):
        login(self.client)

        # Create an editors pick to delete
        self.query = models.Query.get("Hello")
        self.query.editors_picks.create(page_id=1, description="Root page")

    def get(self, params={}):
        return self.client.get('/admin/search/editorspicks/' + str(self.query.id) + '/delete/', params, HTTP_HOST=get_default_host())

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)
