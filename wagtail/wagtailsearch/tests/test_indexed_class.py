from django.test import TestCase
from . import models
import json


class TestContentTypeNames(TestCase):
    def test_base_content_type_name(self):
        name = models.SearchTestChild._get_base_content_type_name()
        self.assertEqual(name, 'tests_searchtest')

    def test_qualified_content_type_name(self):
        name = models.SearchTestChild._get_qualified_content_type_name()
        self.assertEqual(name, 'tests_searchtest_tests_searchtestchild')


class TestGetSearchFields(TestCase):
    def assertDictEqual(self, a, b):
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def test_get_search_fields(self):
        # Get search fields
        search_fields = models.SearchTest.get_search_fields()

        # Check
        expected_result = {
            'id': {
                'filter': True,
                'search': False,
                'type': 'AutoField',
                'attname': 'id'
            },
            'live': {
                'filter': True,
                'search': False,
                'type': 'BooleanField',
                'attname': 'live'
            },
            'title': {
                'filter': True,
                'search': True,
                'type': 'CharField',
                'attname': 'title',
                'boost': None,
                'partial_match': True,
                'es_extra': {}
            },
            'callable_indexed_field': {
                'filter': False,
                'search': True,
                'boost': None,
                'partial_match': False,
                'es_extra': {}
            },
            'content': {
                'filter': False,
                'search': True,
                'type': 'TextField',
                'attname': 'content',
                'boost': None,
                'partial_match': False,
                'es_extra': {}
            },
            'published_date': {
                'filter': True,
                'search': False,
                'type': 'DateField',
                'attname': 'published_date'
            },
        }

        self.assertDictEqual(search_fields, expected_result)

    def test_get_search_fields_inheritance(self):
        # Get search fields
        search_fields = models.SearchTestChild.get_search_fields()

        # Check
        expected_result = {
            'searchtest_ptr': {
                'filter': True,
                'search': False,
                'type': 'OneToOneField',
                'attname': 'searchtest_ptr_id'
            },
            'subtitle': {
                'filter': False,
                'search': True,
                'type': 'CharField',
                'attname': 'subtitle',
                'boost': None,
                'partial_match': True,
                'es_extra': {}
            },
            'extra_content': {
                'filter': False,
                'search': True,
                'type': 'TextField',
                'attname': 'extra_content',
                'boost': None,
                'partial_match': False,
                'es_extra': {}
            },

            # Inherited
            'live': {
                'filter': True,
                'search': False,
                'type': 'BooleanField',
                'attname': 'live'
            },
            'title': {
                'filter': True,
                'search': True,
                'type': 'CharField',
                'attname': 'title',
                'boost': None,
                'partial_match': True,
                'es_extra': {}
            },
            'callable_indexed_field': {
                'filter': False,
                'search': True,
                'boost': None,
                'partial_match': False,
                'es_extra': {}
            },
            'content': {
                'filter': False,
                'search': True,
                'type': 'TextField',
                'attname': 'content',
                'boost': None,
                'partial_match': False,
                'es_extra': {}
            },
            'published_date': {
                'filter': True,
                'search': False,
                'type': 'DateField',
                'attname': 'published_date'
            },
        }

        self.assertDictEqual(search_fields, expected_result)

    def test_get_search_fields_local(self):
        # Get search fields
        search_fields = models.SearchTestChild.get_search_fields(local=True)

        # Check
        expected_result = {
            'searchtest_ptr': {
                'filter': True,
                'search': False,
                'type': 'OneToOneField',
                'attname': 'searchtest_ptr_id'
            },
            'subtitle': {
                'filter': False,
                'search': True,
                'type': 'CharField',
                'attname': 'subtitle',
                'boost': None,
                'partial_match': True,
                'es_extra': {}
            },
            'extra_content': {
                'filter': False,
                'search': True,
                'type': 'TextField',
                'attname': 'extra_content',
                'boost': None,
                'partial_match': False,
                'es_extra': {}
            },
        }

        self.assertDictEqual(search_fields, expected_result)

    def test_get_search_fields_search_only(self):
        # Get search fields
        search_fields = models.SearchTest.get_search_fields(exclude_filter=True)

        # Check
        expected_result = {
            'title': {
                'filter': True,
                'search': True,
                'type': 'CharField',
                'attname': 'title',
                'boost': None,
                'partial_match': True,
                'es_extra': {}
            },
            'callable_indexed_field': {
                'filter': False,
                'search': True,
                'boost': None,
                'partial_match': False,
                'es_extra': {}
            },
            'content': {
                'filter': False,
                'search': True,
                'type': 'TextField',
                'attname': 'content',
                'boost': None,
                'partial_match': False,
                'es_extra': {}
            },
        }

        self.assertDictEqual(search_fields, expected_result)

    def test_get_search_fields_filter_only(self):
        # Get search fields
        search_fields = models.SearchTest.get_search_fields(exclude_search=True)

        # Check
        expected_result = {
            'id': {
                'filter': True,
                'search': False,
                'type': 'AutoField',
                'attname': 'id'
            },
            'live': {
                'filter': True,
                'search': False,
                'type': 'BooleanField',
                'attname': 'live'
            },
            'title': {
                'filter': True,
                'search': True,
                'type': 'CharField',
                'attname': 'title',
                'boost': None,
                'partial_match': True,
                'es_extra': {}
            },
            'published_date': {
                'filter': True,
                'search': False,
                'type': 'DateField',
                'attname': 'published_date'
            },
        }

        self.assertDictEqual(search_fields, expected_result)


class TestIndexedFieldsBackwardsCompatibility(TestCase):
    def assertDictEqual(self, a, b):
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def test_indexed_fields_backwards_compatibility(self):
        # Get search fields
        search_fields = models.SearchTestOldConfig.get_search_fields()

        # Check
        expected_result = {
            'id': {
                'filter': True,
                'search': False,
                'type': 'AutoField',
                'attname': 'id'
            },
            'live': {
                'filter': True,
                'search': False
            },
            'title': {
                'search': True,
                'filter': False,
                'partial_match': True,
                'boost': 100,
                'es_extra': {'type': 'string'}
            },
        }

        self.assertDictEqual(search_fields, expected_result)

    def test_indexed_fields_backwards_compatibility_list(self):
        # Get search fields
        search_fields = models.SearchTestOldConfigList.get_search_fields()

        # Check
        expected_result = {
            'id': {
                'filter': True,
                'search': False,
                'type': 'AutoField',
                'attname': 'id'
            },
            'title': {
                'search': True,
                'filter': False,
                'boost': None,
                'partial_match': False,
                'es_extra': {}
            },
            'content': {
                'search': True,
                'filter': False,
                'boost': None,
                'partial_match': False,
                'es_extra': {}
            },
        }

        self.assertDictEqual(search_fields, expected_result)
