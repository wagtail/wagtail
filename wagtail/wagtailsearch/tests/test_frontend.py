from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core import paginator

from wagtail.wagtailcore.models import Page
from wagtail.wagtailsearch.models import Query

from wagtail.tests.testapp.models import EventPage


class TestSearchView(TestCase):
    fixtures = ['test.json']

    def test_get(self):
        response = self.client.get(reverse('wagtailsearch_search'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearch/search_results.html')

        # Check that search_results/query are set to None
        self.assertIsNone(response.context['search_results'])
        self.assertIsNone(response.context['query'])

    def test_search(self):
        response = self.client.get(reverse('wagtailsearch_search') + '?q=Christmas')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearch/search_results.html')
        self.assertEqual(response.context['query_string'], "Christmas")

        # Check that search_results is an instance of paginator.Page
        self.assertIsInstance(response.context['search_results'], paginator.Page)

        # Check that the christmas page was in the results (and is the only result)
        search_results = response.context['search_results'].object_list
        christmas_event_page = Page.objects.get(url_path='/home/events/christmas/')
        self.assertEqual(list(search_results), [christmas_event_page])

        # Check the query object
        self.assertIsInstance(response.context['query'], Query)
        query = response.context['query']
        self.assertEqual(query.query_string, "christmas")

    def pagination_test(test):
        def wrapper(*args, **kwargs):
            # Create some pages
            event_index = Page.objects.get(url_path='/home/events/')
            for i in range(100):
                event = EventPage(
                    title="Event " + str(i),
                    slug='event-' + str(i),
                    live=True,
                )
                event_index.add_child(instance=event)

            return test(*args, **kwargs)

        return wrapper

    @pagination_test
    def test_get_first_page(self):
        response = self.client.get(reverse('wagtailsearch_search') + '?q=Event&page=1')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearch/search_results.html')

        # Test that we got the first page
        search_results = response.context['search_results']
        self.assertEqual(search_results.number, 1)

    @pagination_test
    def test_get_10th_page(self):
        response = self.client.get(reverse('wagtailsearch_search') + '?q=Event&page=10')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearch/search_results.html')

        # Test that we got the tenth page
        search_results = response.context['search_results']
        self.assertEqual(search_results.number, 10)

    @pagination_test
    def test_get_invalid_page(self):
        response = self.client.get(reverse('wagtailsearch_search') + '?q=Event&page=Not a Page')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearch/search_results.html')

        # Test that we got the first page
        search_results = response.context['search_results']
        self.assertEqual(search_results.number, 1)

    @pagination_test
    def test_get_out_of_range_page(self):
        response = self.client.get(reverse('wagtailsearch_search') + '?q=Event&page=9999')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearch/search_results.html')

        # Test that we got the last page
        search_results = response.context['search_results']
        self.assertEqual(search_results.number, search_results.paginator.num_pages)

    @pagination_test
    def test_get_zero_page(self):
        response = self.client.get(reverse('wagtailsearch_search') + '?q=Event&page=0')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearch/search_results.html')

        # Test that we got the first page
        search_results = response.context['search_results']
        self.assertEqual(search_results.number, search_results.paginator.num_pages)

    @pagination_test
    def test_get_10th_page_backwards_compatibility_with_p(self):
        response = self.client.get(reverse('wagtailsearch_search') + '?q=Event&p=10')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearch/search_results.html')

        # Test that we got the tenth page
        search_results = response.context['search_results']
        self.assertEqual(search_results.number, 10)


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
