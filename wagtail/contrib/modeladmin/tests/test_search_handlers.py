from unittest.mock import patch

from django.test import TestCase

from wagtail.contrib.modeladmin.helpers import DjangoORMSearchHandler, WagtailBackendSearchHandler
from wagtail.tests.modeladmintest.models import Book


class FakeBackend():
    def search(
            self, query, model_or_queryset, fields=None, operator=None, order_by_relevance=True, partial_match=True):
        return {
            'fields': fields,
            'operator': operator,
            'order_by_relevance': order_by_relevance,
            'partial_match': partial_match
        }


class TestORMSearchHandler(TestCase):
    fixtures = ['modeladmintest_test.json']

    def get_search_handler(self, search_fields=None):
        return DjangoORMSearchHandler(search_fields)

    def get_search_queryset(self):
        return Book.objects.all()

    def test_search_queryset(self):
        search_handler = self.get_search_handler()
        # No search fields, return same queryset
        results = search_handler.search_queryset(self.get_search_queryset(), 'Lord')
        self.assertEqual(list(self.get_search_queryset()), list(results))

        search_handler = self.get_search_handler(search_fields=('title',))
        # No search_term, return same, queryset
        results = search_handler.search_queryset(self.get_search_queryset(), '')
        self.assertEqual(list(self.get_search_queryset()), list(results))

        lord_of_the_rings = Book.objects.filter(pk=1)
        results = search_handler.search_queryset(self.get_search_queryset(), 'Lord of the rings')
        self.assertEqual(list(lord_of_the_rings), list(results))



    def test_show_search_form(self):
        search_handler = self.get_search_handler(search_fields=None)
        self.assertFalse(search_handler.show_search_form)

        search_handler = self.get_search_handler(search_fields=('content',))
        self.assertTrue(search_handler.show_search_form)


class TestSearchBackendHandler(TestCase):
    def get_search_handler(self, search_fields=None):
        return WagtailBackendSearchHandler(search_fields)

    def search_kwargs_to_dict(self, search_fields=None, operator=None, order_by_relevance=False, partial_match=True):
        return {
            'fields': search_fields,
            'operator': operator,
            'order_by_relevance': order_by_relevance,
            'partial_match': partial_match
        }

    @patch('wagtail.contrib.modeladmin.helpers.search.get_search_backend', return_value=FakeBackend())
    def test_search_queryset(self, get_search_backend):
        search_queryset = Book.objects.all()

        # Test default backend kwargs
        search_handler = self.get_search_handler()
        search_kwargs = search_handler.search_queryset(search_queryset, 'Lord')

        self.assertEqual(self.search_kwargs_to_dict(), search_kwargs)

        # Test search_fields
        search_fields = ('content',)
        search_handler = self.get_search_handler(search_fields=search_fields)
        self.assertEqual(self.search_kwargs_to_dict(search_fields=search_fields),
                         search_handler.search_queryset(search_queryset, 'Lord'))

        # Test other kwargs
        self.assertEqual(
            self.search_kwargs_to_dict(search_fields=search_fields, operator='and', partial_match=False, order_by_relevance=True),
            search_handler.search_queryset(search_queryset, 'Lord', operator='and', order_by_relevance=True, partial_match=False)
        )

    def test_show_search_form(self):
        search_handler = self.get_search_handler(search_fields=None)
        self.assertTrue(search_handler.show_search_form)

        search_handler = self.get_search_handler(search_fields=('content',))
        self.assertTrue(search_handler.show_search_form)
