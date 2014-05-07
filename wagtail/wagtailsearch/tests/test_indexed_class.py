from django.test import TestCase
from . import models
import json


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
                'predictive': True,
                'boost': 100,
                'es_extra': {'type': 'string'}
            }
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
            },
            'content': {
                'search': True,
                'filter': False,
            }
        }

        self.assertDictEqual(search_fields, expected_result)
