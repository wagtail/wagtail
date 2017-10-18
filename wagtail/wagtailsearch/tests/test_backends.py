# coding: utf-8

from __future__ import absolute_import, unicode_literals

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

    fixtures = ['search']

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
            for index, indexed_models in group_models_by_index(self.backend, [models.Author, models.Book, models.Novel]).items():
                rebuilder = self.backend.rebuilder_class(index)
                index = rebuilder.start()
                for model in indexed_models:
                    index.add_model(model)
                rebuilder.finish()

    def refresh_index(self):
        index = self.backend.get_index_for_model(models.Author)
        if index:
            index.refresh()

        index = self.backend.get_index_for_model(models.Book)
        if index:
            index.refresh()

    def load_test_data(self):
        self.reset_index()

        self.refresh_index()

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
