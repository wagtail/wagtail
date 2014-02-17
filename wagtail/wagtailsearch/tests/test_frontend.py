from django.test import TestCase
from .utils import get_default_host


class TestSearchView(TestCase):
    def get(self, params={}):
        return self.client.get('/search/', params, HTTP_HOST=get_default_host())

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_search_status_code(self):
        self.assertEqual(self.get({'q': "Hello"}).status_code, 200)

    def test_search_template_context(self):
        self.assertEqual(self.get({'q': "Hello"}).context['query_string'], "Hello")

    def test_page_status_code(self):
        self.assertEqual(self.get({'p': '1'}).status_code, 200)


class TestSuggestionsView(TestCase):
    def get(self, params={}):
        return self.client.get('/search/suggest/', params, HTTP_HOST=get_default_host())

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_search_status_code(self):
        self.assertEqual(self.get({'q': "Hello"}).status_code, 200)
