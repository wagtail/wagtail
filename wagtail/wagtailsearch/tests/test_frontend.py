from django.test import TestCase


class TestSearchView(TestCase):
    def get(self, params={}):
        return self.client.get('/search/', params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearch/search_results.html')

    def test_search(self):
        response = self.get({'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

    def test_pagination(self):
        pages = ['0', '1', '-1', '9999', 'Not a page']
        for page in pages:
            response = self.get({'p': page})
            self.assertEqual(response.status_code, 200)


class TestSuggestionsView(TestCase):
    def get(self, params={}):
        return self.client.get('/search/suggest/', params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        # TODO: Check that a valid JSON document was returned

    def test_search(self):
        response = self.get({'q': "Hello"})
        self.assertEqual(response.status_code, 200)
