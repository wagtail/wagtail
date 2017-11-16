# coding: utf-8

from __future__ import absolute_import, unicode_literals

import datetime
import time
import unittest

from django.conf import settings
from django.core import management
from django.test import TestCase
from django.test.utils import override_settings
from django.utils.six import StringIO

from wagtail.tests.search import models
from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailsearch.backends import (
    InvalidSearchBackendError, get_search_backend, get_search_backends)
from wagtail.wagtailsearch.backends.base import FieldError
from wagtail.wagtailsearch.backends.db import DatabaseSearchBackend
from wagtail.wagtailsearch.management.commands.update_index import group_models_by_index


class BackendTests(WagtailTestUtils):
    # To test a specific backend, subclass BackendTests and define self.backend_path.

    def setUp(self):
        # Search WAGTAILSEARCH_BACKENDS for an entry that uses the given backend path
        for backend_name, backend_conf in settings.WAGTAILSEARCH_BACKENDS.items():
            if backend_conf['BACKEND'] == self.backend_path:
                self.backend = get_search_backend(backend_name)
                self.backend_name = backend_name
                break
        else:
            # no conf entry found - skip tests for this backend
            raise unittest.SkipTest("No WAGTAILSEARCH_BACKENDS entry for the backend %s" % self.backend_path)

        self.load_test_data()

    def reset_index(self):
        if self.backend.rebuilder_class:
            for index, indexed_models in group_models_by_index(self.backend, [models.SearchTest, models.SearchTestChild]).items():
                rebuilder = self.backend.rebuilder_class(index)
                index = rebuilder.start()
                for model in indexed_models:
                    index.add_model(model)
                rebuilder.finish()

    def refresh_index(self):
        index = self.backend.get_index_for_model(models.SearchTest)
        if index:
            index.refresh()

    def load_test_data(self):
        self.reset_index()

        # Create a test database
        testa = models.SearchTest()
        testa.title = "Hello World"
        testa.published_date = datetime.date(2015, 10, 11)
        testa.save()
        testa.subobjects.create(name='A subobject')
        self.backend.add(testa)
        self.testa = testa

        testb = models.SearchTest()
        testb.title = "Hello"
        testb.live = True
        testb.save()
        self.backend.add(testb)
        self.testb = testb

        testc = models.SearchTestChild()
        testc.title = "Hello Kitty"
        testc.live = True
        testc.content = "Hello"
        testc.subtitle = "Foo"
        testc.save()
        self.backend.add(testc)
        self.testc = testc

        testd = models.SearchTestChild()
        testd.title = "World"
        testd.subtitle = "Foo"
        testd.save()
        self.backend.add(testd)
        self.testd = testd

        self.refresh_index()

    def test_blank_search(self):
        results = self.backend.search("", models.SearchTest)
        self.assertEqual(set(results), set())

    def test_search(self):
        results = self.backend.search("Hello", models.SearchTest)
        self.assertEqual(set(results), {self.testa, self.testb, self.testc.searchtest_ptr})

        results = self.backend.search("World", models.SearchTest)
        self.assertEqual(set(results), {self.testa, self.testd.searchtest_ptr})

    def test_individual_field(self):
        results = self.backend.search("Hello", models.SearchTest, fields=['content'])
        self.assertEqual(set(results), {self.testc.searchtest_ptr})

    def test_individual_field_in_child_class(self):
        results = self.backend.search("Foo", models.SearchTestChild, fields=['subtitle'])
        self.assertEqual(set(results), {self.testc, self.testd})

    def test_unknown_field_gives_error(self):
        self.assertRaises(FieldError, self.backend.search, "Hello Bar", models.SearchTestChild, fields=['unknown'])

    def test_child_field_from_parent_gives_error(self):
        self.assertRaises(FieldError, self.backend.search, "Hello", models.SearchTest, fields=['subtitle'])

    def test_operator_or(self):
        # All records that match any term should be returned
        results = self.backend.search("Hello world", models.SearchTest, operator='or')

        self.assertEqual(set(results), {self.testa, self.testb, self.testc.searchtest_ptr, self.testd.searchtest_ptr})

    def test_operator_and(self):
        # Records must match all search terms to be returned
        results = self.backend.search("Hello world", models.SearchTest, operator='and')

        self.assertEqual(set(results), {self.testa})

    def test_callable_indexed_field(self):
        results = self.backend.search("Callable", models.SearchTest)
        self.assertEqual(set(results), {self.testa, self.testb, self.testc.searchtest_ptr, self.testd.searchtest_ptr})

    def test_filters(self):
        results = self.backend.search(None, models.SearchTest, filters=dict(live=True))
        self.assertEqual(set(results), {self.testb, self.testc.searchtest_ptr})

    def test_filter_isnull_true(self):
        results = self.backend.search(None, models.SearchTest, filters=dict(published_date__isnull=True))
        self.assertEqual(set(results), {self.testb, self.testc.searchtest_ptr, self.testd.searchtest_ptr})

    def test_filter_isnull_false(self):
        results = self.backend.search(None, models.SearchTest, filters=dict(published_date__isnull=False))
        self.assertEqual(set(results), {self.testa})

    def test_filters_in_subquery(self):
        live_page_titles = models.SearchTest.objects.filter(live=True).values_list('title', flat=True)
        results = self.backend.search(None, models.SearchTest, filters=dict(title__in=live_page_titles))
        self.assertEqual(set(results), {self.testb, self.testc.searchtest_ptr})

    def test_filters_in_list(self):
        live_page_titles = ['Hello', 'Hello Kitty']
        results = self.backend.search(None, models.SearchTest,
                                      filters=dict(title__in=live_page_titles))
        self.assertEqual(set(results), {self.testb, self.testc.searchtest_ptr})

    def test_filters_in_iterable(self):
        class CustomIterable:
            def __init__(self, data):
                self.data = data

            def __iter__(self):
                for item in self.data:
                    yield item

        results = self.backend.search(
            None, models.SearchTest,
            filters=dict(title__in=CustomIterable(['World'])))
        self.assertEqual(set(results), {self.testd.searchtest_ptr})

    def test_single_result(self):
        result = self.backend.search(None, models.SearchTest)[0]
        self.assertIsInstance(result, models.SearchTest)

    def test_sliced_results(self):
        sliced_results = self.backend.search(None, models.SearchTest)[1:3]

        self.assertEqual(len(sliced_results), 2)

        for result in sliced_results:
            self.assertIsInstance(result, models.SearchTest)

    def test_child_model(self):
        results = self.backend.search(None, models.SearchTestChild)
        self.assertEqual(set(results), {self.testc, self.testd})

    def test_child_model_with_id_filter(self):
        results = self.backend.search("World", models.SearchTestChild.objects.filter(id=self.testd.id))
        self.assertEqual(set(results), {self.testd})

    def test_related_objects_search(self):
        results = self.backend.search("A subobject", models.SearchTest)
        self.assertEqual(set(results), {self.testa})

    def test_boost(self):
        results = list(self.backend.search('Hello', models.SearchTest))
        # The `content` field has more boost, so the object containing “Hello”
        # should be before the ones having it in the title,
        # despite the insertion order.
        self.assertEqual(results[0], self.testc.searchtest_ptr)
        self.assertSetEqual(set(results[1:]), {self.testa, self.testb})

    def test_order_by_relevance(self):
        sorted_results = list(self.backend.search('Hello', models.SearchTest,
                                                  order_by_relevance=True))
        self.assertEqual(sorted_results[0], self.testc.searchtest_ptr)
        self.assertSetEqual(set(sorted_results[1:]), {self.testa, self.testb})

        unsorted_results = list(self.backend.search('Hello', models.SearchTest,
                                                    order_by_relevance=False))
        self.assertSetEqual(
            set(unsorted_results),
            {self.testa, self.testb, self.testc.searchtest_ptr})

    def test_same_rank_pages(self):
        """
        Checks that results with a same ranking cannot be found multiple times
        across pages (see issue #3729).
        """
        same_rank_objects = set()
        try:
            for i in range(10):
                obj = models.SearchTest.objects.create(title='Rank %s' % i)
                self.backend.add(obj)
                same_rank_objects.add(obj)
            self.refresh_index()

            results = self.backend.search('Rank', models.SearchTest)
            results_across_pages = set()
            for i, obj in enumerate(same_rank_objects):
                results_across_pages.add(results[i:i + 1][0])
            self.assertSetEqual(results_across_pages, same_rank_objects)
        finally:
            for obj in same_rank_objects:
                self.backend.delete(obj)
                obj.delete()
            self.refresh_index()

    def test_delete(self):
        # Delete one of the objects
        self.backend.delete(self.testa)
        self.testa.delete()
        self.refresh_index()

        results = self.backend.search(None, models.SearchTest)
        self.assertEqual(set(results), {self.testb, self.testc.searchtest_ptr, self.testd.searchtest_ptr})

    def test_update_index_command(self):
        # Reset the index, this should clear out the index
        self.reset_index()

        # Give Elasticsearch some time to catch up...
        time.sleep(1)

        results = self.backend.search(None, models.SearchTest)
        self.assertEqual(set(results), set())

        # Run update_index command
        with self.ignore_deprecation_warnings():
            # ignore any DeprecationWarnings thrown by models with old-style indexed_fields definitions
            management.call_command(
                'update_index', backend_name=self.backend_name, interactive=False, stdout=StringIO()
            )

        results = self.backend.search(None, models.SearchTest)
        self.assertEqual(set(results), {self.testa, self.testb, self.testc.searchtest_ptr, self.testd.searchtest_ptr})


@override_settings(
    WAGTAILSEARCH_BACKENDS={
        'default': {'BACKEND': 'wagtail.wagtailsearch.backends.db'}
    }
)
class TestBackendLoader(TestCase):
    def test_import_by_name(self):
        db = get_search_backend(backend='default')
        self.assertIsInstance(db, DatabaseSearchBackend)

    def test_import_by_path(self):
        db = get_search_backend(backend='wagtail.wagtailsearch.backends.db')
        self.assertIsInstance(db, DatabaseSearchBackend)

    def test_import_by_full_path(self):
        db = get_search_backend(backend='wagtail.wagtailsearch.backends.db.DatabaseSearchBackend')
        self.assertIsInstance(db, DatabaseSearchBackend)

    def test_nonexistent_backend_import(self):
        self.assertRaises(
            InvalidSearchBackendError, get_search_backend, backend='wagtail.wagtailsearch.backends.doesntexist'
        )

    def test_invalid_backend_import(self):
        self.assertRaises(InvalidSearchBackendError, get_search_backend, backend="I'm not a backend!")

    def test_get_search_backends(self):
        backends = list(get_search_backends())

        self.assertEqual(len(backends), 1)
        self.assertIsInstance(backends[0], DatabaseSearchBackend)

    @override_settings(
        WAGTAILSEARCH_BACKENDS={}
    )
    def test_get_search_backends_with_no_default_defined(self):
        backends = list(get_search_backends())

        self.assertEqual(len(backends), 1)
        self.assertIsInstance(backends[0], DatabaseSearchBackend)

    @override_settings(
        WAGTAILSEARCH_BACKENDS={
            'default': {
                'BACKEND': 'wagtail.wagtailsearch.backends.db'
            },
            'another-backend': {
                'BACKEND': 'wagtail.wagtailsearch.backends.db'
            },
        }
    )
    def test_get_search_backends_multiple(self):
        backends = list(get_search_backends())

        self.assertEqual(len(backends), 2)

    def test_get_search_backends_with_auto_update(self):
        backends = list(get_search_backends(with_auto_update=True))

        # Auto update is the default
        self.assertEqual(len(backends), 1)

    @override_settings(
        WAGTAILSEARCH_BACKENDS={
            'default': {
                'BACKEND': 'wagtail.wagtailsearch.backends.db',
                'AUTO_UPDATE': False,
            },
        }
    )
    def test_get_search_backends_with_auto_update_disabled(self):
        backends = list(get_search_backends(with_auto_update=True))

        self.assertEqual(len(backends), 0)

    @override_settings(
        WAGTAILSEARCH_BACKENDS={
            'default': {
                'BACKEND': 'wagtail.wagtailsearch.backends.db',
                'AUTO_UPDATE': False,
            },
        }
    )
    def test_get_search_backends_without_auto_update_disabled(self):
        backends = list(get_search_backends())

        self.assertEqual(len(backends), 1)
