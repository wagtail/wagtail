from unittest.mock import patch

from django.test import TestCase

from wagtail.contrib.modeladmin.helpers import (
    DjangoORMSearchHandler,
    WagtailBackendSearchHandler,
)
from wagtail.test.modeladmintest.models import Book


class FakeSearchBackend:

    search_last_called_with = None

    def search(
        self,
        query,
        model_or_queryset,
        fields=None,
        operator=None,
        order_by_relevance=True,
    ):
        return {
            "query": query,
            "model_or_queryset": model_or_queryset,
            "fields": fields,
            "operator": operator,
            "order_by_relevance": order_by_relevance,
        }


class TestORMSearchHandler(TestCase):
    fixtures = ["modeladmintest_test.json"]

    def get_search_handler(self, search_fields=None):
        return DjangoORMSearchHandler(search_fields)

    def get_queryset(self):
        return Book.objects.all()

    def test_search_queryset_no_search_query(self):
        # When no search fields are specified, DjangoORMSearchHandler
        # returns the queryset that was passed to it
        search_handler = self.get_search_handler(search_fields=("title",))
        queryset = self.get_queryset()
        result = search_handler.search_queryset(queryset, "")
        self.assertIs(result, queryset)

    def test_search_queryset_no_search_fields(self):
        # When the search query is blank, DjangoORMSearchHandler
        # returns the queryset that was passed to it
        search_handler = self.get_search_handler()
        queryset = self.get_queryset()
        result = search_handler.search_queryset(queryset, "Lord")
        self.assertIs(result, queryset)

    def test_search_queryset(self):
        search_handler = self.get_search_handler(search_fields=("title",))
        queryset = self.get_queryset()
        expected_result = queryset.filter(pk=1)
        result = search_handler.search_queryset(queryset, "Lord of the rings")
        self.assertEqual(list(expected_result), list(result))

    def test_show_search_form(self):
        search_handler = self.get_search_handler(search_fields=None)
        self.assertFalse(search_handler.show_search_form)

        search_handler = self.get_search_handler(search_fields=("content",))
        self.assertTrue(search_handler.show_search_form)


class TestSearchBackendHandler(TestCase):
    def get_search_handler(self, search_fields=None):
        return WagtailBackendSearchHandler(search_fields)

    def get_queryset(self):
        return Book.objects.all()

    @patch(
        "wagtail.contrib.modeladmin.helpers.search.get_search_backend",
        return_value=FakeSearchBackend(),
    )
    def test_search_queryset_no_search_query(self, mocked_method):
        # When the search query is blank, WagtailBackendSearchHandler
        # returns the queryset that was passed to it
        search_handler = self.get_search_handler(search_fields=("title",))
        queryset = self.get_queryset()
        result = search_handler.search_queryset(queryset, "")
        self.assertIs(result, queryset)

    @patch(
        "wagtail.contrib.modeladmin.helpers.search.get_search_backend",
        return_value=FakeSearchBackend(),
    )
    def test_search_queryset_no_search_fields(self, mocked_method):
        # When no search fields are specified, WagtailBackendSearchHandler
        # searches on all indexed fields
        search_handler = self.get_search_handler()
        queryset = self.get_queryset()
        search_kwargs = search_handler.search_queryset(queryset, "test")
        self.assertTrue(mocked_method.called)
        self.assertEqual(
            search_kwargs,
            {
                "query": "test",
                "model_or_queryset": queryset,
                "fields": None,
                "operator": None,
                "order_by_relevance": True,
            },
        )

    @patch(
        "wagtail.contrib.modeladmin.helpers.search.get_search_backend",
        return_value=FakeSearchBackend(),
    )
    def test_search_queryset_with_search_fields(self, mocked_method):
        # When no search fields are specified, WagtailBackendSearchHandler
        # searches on all indexed fields
        search_fields = ("field1", "field2")
        search_handler = self.get_search_handler(search_fields)
        queryset = self.get_queryset()
        search_kwargs = search_handler.search_queryset(queryset, "test")
        self.assertTrue(mocked_method.called)
        self.assertEqual(
            search_kwargs,
            {
                "query": "test",
                "model_or_queryset": queryset,
                "fields": search_fields,
                "operator": None,
                "order_by_relevance": True,
            },
        )

    @patch(
        "wagtail.contrib.modeladmin.helpers.search.get_search_backend",
        return_value=FakeSearchBackend(),
    )
    def test_search_queryset_preserve_order(self, get_search_backend):
        search_handler = self.get_search_handler()
        queryset = self.get_queryset()

        search_kwargs = search_handler.search_queryset(
            queryset, "Lord", preserve_order=True
        )
        self.assertEqual(
            search_kwargs,
            {
                "query": "Lord",
                "model_or_queryset": queryset,
                "fields": None,
                "operator": None,
                "order_by_relevance": False,
            },
        )

    def test_show_search_form(self):
        search_handler = self.get_search_handler(search_fields=None)
        self.assertTrue(search_handler.show_search_form)

        search_handler = self.get_search_handler(search_fields=("content",))
        self.assertTrue(search_handler.show_search_form)
