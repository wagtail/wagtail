from __future__ import absolute_import, unicode_literals

import json

import mock
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from wagtail.contrib.wagtailapi import signal_handlers
from wagtail.wagtaildocs.models import get_document_model


class TestDocumentListing(TestCase):
    fixtures = ['demosite.json']

    def get_response(self, **params):
        return self.client.get(reverse('wagtailapi_v1:documents:listing'), params)

    def get_document_id_list(self, content):
        return [page['id'] for page in content['documents']]


    # BASIC TESTS

    def test_basic(self):
        response = self.get_response()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-type'], 'application/json')

        # Will crash if the JSON is invalid
        content = json.loads(response.content.decode('UTF-8'))

        # Check that the meta section is there
        self.assertIn('meta', content)
        self.assertIsInstance(content['meta'], dict)

        # Check that the total count is there and correct
        self.assertIn('total_count', content['meta'])
        self.assertIsInstance(content['meta']['total_count'], int)
        self.assertEqual(content['meta']['total_count'], get_document_model().objects.count())

        # Check that the documents section is there
        self.assertIn('documents', content)
        self.assertIsInstance(content['documents'], list)

        # Check that each document has a meta section with type and detail_url attributes
        for document in content['documents']:
            self.assertIn('meta', document)
            self.assertIsInstance(document['meta'], dict)
            self.assertEqual(set(document['meta'].keys()), {'type', 'detail_url'})

            # Type should always be wagtaildocs.Document
            self.assertEqual(document['meta']['type'], 'wagtaildocs.Document')

            # Check detail_url
            self.assertEqual(document['meta']['detail_url'], 'http://localhost/api/v1/documents/%d/' % document['id'])


    # EXTRA FIELDS

    def test_extra_fields_default(self):
        response = self.get_response()
        content = json.loads(response.content.decode('UTF-8'))

        for document in content['documents']:
            self.assertEqual(set(document.keys()), {'id', 'meta', 'title'})

    def test_extra_fields(self):
        response = self.get_response(fields='title,tags')
        content = json.loads(response.content.decode('UTF-8'))

        for document in content['documents']:
            self.assertEqual(set(document.keys()), {'id', 'meta', 'title', 'tags'})

    def test_extra_fields_tags(self):
        response = self.get_response(fields='tags')
        content = json.loads(response.content.decode('UTF-8'))

        for document in content['documents']:
            self.assertIsInstance(document['tags'], list)

    def test_extra_fields_which_are_not_in_api_fields_gives_error(self):
        response = self.get_response(fields='uploaded_by_user')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "unknown fields: uploaded_by_user"})

    def test_extra_fields_unknown_field_gives_error(self):
        response = self.get_response(fields='123,title,abc')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "unknown fields: 123, abc"})


    # FILTERING

    def test_filtering_exact_filter(self):
        response = self.get_response(title='James Joyce')
        content = json.loads(response.content.decode('UTF-8'))

        document_id_list = self.get_document_id_list(content)
        self.assertEqual(document_id_list, [2])

    def test_filtering_on_id(self):
        response = self.get_response(id=10)
        content = json.loads(response.content.decode('UTF-8'))

        document_id_list = self.get_document_id_list(content)
        self.assertEqual(document_id_list, [10])

    def test_filtering_tags(self):
        get_document_model().objects.get(id=3).tags.add('test')

        response = self.get_response(tags='test')
        content = json.loads(response.content.decode('UTF-8'))

        document_id_list = self.get_document_id_list(content)
        self.assertEqual(document_id_list, [3])

    def test_filtering_unknown_field_gives_error(self):
        response = self.get_response(not_a_field='abc')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "query parameter is not an operation or a recognised field: not_a_field"})


    # ORDERING

    def test_ordering_by_title(self):
        response = self.get_response(order='title')
        content = json.loads(response.content.decode('UTF-8'))

        document_id_list = self.get_document_id_list(content)
        self.assertEqual(document_id_list, [3, 12, 10, 2, 7, 8, 5, 4, 1, 11, 9, 6])

    def test_ordering_by_title_backwards(self):
        response = self.get_response(order='-title')
        content = json.loads(response.content.decode('UTF-8'))

        document_id_list = self.get_document_id_list(content)
        self.assertEqual(document_id_list, [6, 9, 11, 1, 4, 5, 8, 7, 2, 10, 12, 3])

    def test_ordering_by_random(self):
        response_1 = self.get_response(order='random')
        content_1 = json.loads(response_1.content.decode('UTF-8'))
        document_id_list_1 = self.get_document_id_list(content_1)

        response_2 = self.get_response(order='random')
        content_2 = json.loads(response_2.content.decode('UTF-8'))
        document_id_list_2 = self.get_document_id_list(content_2)

        self.assertNotEqual(document_id_list_1, document_id_list_2)

    def test_ordering_by_random_backwards_gives_error(self):
        response = self.get_response(order='-random')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "cannot order by 'random' (unknown field)"})

    def test_ordering_by_random_with_offset_gives_error(self):
        response = self.get_response(order='random', offset=10)
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "random ordering with offset is not supported"})

    def test_ordering_by_unknown_field_gives_error(self):
        response = self.get_response(order='not_a_field')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "cannot order by 'not_a_field' (unknown field)"})


    # LIMIT

    def test_limit_only_two_results_returned(self):
        response = self.get_response(limit=2)
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(len(content['documents']), 2)

    def test_limit_total_count(self):
        response = self.get_response(limit=2)
        content = json.loads(response.content.decode('UTF-8'))

        # The total count must not be affected by "limit"
        self.assertEqual(content['meta']['total_count'], get_document_model().objects.count())

    def test_limit_not_integer_gives_error(self):
        response = self.get_response(limit='abc')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "limit must be a positive integer"})

    def test_limit_too_high_gives_error(self):
        response = self.get_response(limit=1000)
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "limit cannot be higher than 20"})

    @override_settings(WAGTAILAPI_LIMIT_MAX=10)
    def test_limit_maximum_can_be_changed(self):
        response = self.get_response(limit=20)
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "limit cannot be higher than 10"})

    @override_settings(WAGTAILAPI_LIMIT_MAX=2)
    def test_limit_default_changes_with_max(self):
        # The default limit is 20. If WAGTAILAPI_LIMIT_MAX is less than that,
        # the default should change accordingly.
        response = self.get_response()
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(len(content['documents']), 2)


    # OFFSET

    def test_offset_5_usually_appears_5th_in_list(self):
        response = self.get_response()
        content = json.loads(response.content.decode('UTF-8'))
        document_id_list = self.get_document_id_list(content)
        self.assertEqual(document_id_list.index(5), 4)

    def test_offset_5_moves_after_offset(self):
        response = self.get_response(offset=4)
        content = json.loads(response.content.decode('UTF-8'))
        document_id_list = self.get_document_id_list(content)
        self.assertEqual(document_id_list.index(5), 0)

    def test_offset_total_count(self):
        response = self.get_response(offset=10)
        content = json.loads(response.content.decode('UTF-8'))

        # The total count must not be affected by "offset"
        self.assertEqual(content['meta']['total_count'], get_document_model().objects.count())

    def test_offset_not_integer_gives_error(self):
        response = self.get_response(offset='abc')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "offset must be a positive integer"})


    # SEARCH

    def test_search_for_james_joyce(self):
        response = self.get_response(search='james')
        content = json.loads(response.content.decode('UTF-8'))

        document_id_list = self.get_document_id_list(content)

        self.assertEqual(set(document_id_list), set([2]))

    def test_search_when_ordering_gives_error(self):
        response = self.get_response(search='james', order='title')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "ordering with a search query is not supported"})

    @override_settings(WAGTAILAPI_SEARCH_ENABLED=False)
    def test_search_when_disabled_gives_error(self):
        response = self.get_response(search='james')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "search is disabled"})

    def test_search_when_filtering_by_tag_gives_error(self):
        response = self.get_response(search='james', tags='wagtail')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "filtering by tag with a search query is not supported"})


class TestDocumentDetail(TestCase):
    fixtures = ['demosite.json']

    def get_response(self, image_id, **params):
        return self.client.get(reverse('wagtailapi_v1:documents:detail', args=(image_id, )), params)

    def test_basic(self):
        response = self.get_response(1)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-type'], 'application/json')

        # Will crash if the JSON is invalid
        content = json.loads(response.content.decode('UTF-8'))

        # Check the id field
        self.assertIn('id', content)
        self.assertEqual(content['id'], 1)

        # Check that the meta section is there
        self.assertIn('meta', content)
        self.assertIsInstance(content['meta'], dict)

        # Check the meta type
        self.assertIn('type', content['meta'])
        self.assertEqual(content['meta']['type'], 'wagtaildocs.Document')

        # Check the meta detail_url
        self.assertIn('detail_url', content['meta'])
        self.assertEqual(content['meta']['detail_url'], 'http://localhost/api/v1/documents/1/')

        # Check the meta download_url
        self.assertIn('download_url', content['meta'])
        self.assertEqual(content['meta']['download_url'], 'http://localhost/documents/1/wagtail_by_markyharky.jpg')

        # Check the title field
        self.assertIn('title', content)
        self.assertEqual(content['title'], "Wagtail by mark Harkin")

        # Check the tags field
        self.assertIn('tags', content)
        self.assertEqual(content['tags'], [])

    def test_tags(self):
        get_document_model().objects.get(id=1).tags.add('hello')
        get_document_model().objects.get(id=1).tags.add('world')

        response = self.get_response(1)
        content = json.loads(response.content.decode('UTF-8'))

        self.assertIn('tags', content)
        self.assertEqual(content['tags'], ['hello', 'world'])

    @override_settings(WAGTAILAPI_BASE_URL='http://api.example.com/')
    def test_download_url_with_custom_base_url(self):
        response = self.get_response(1)
        content = json.loads(response.content.decode('UTF-8'))

        self.assertIn('download_url', content['meta'])
        self.assertEqual(
            content['meta']['download_url'], 'http://api.example.com/documents/1/wagtail_by_markyharky.jpg'
        )


@override_settings(
    WAGTAILFRONTENDCACHE={
        'varnish': {
            'BACKEND': 'wagtail.contrib.wagtailfrontendcache.backends.HTTPBackend',
            'LOCATION': 'http://localhost:8000',
        },
    },
    WAGTAILAPI_BASE_URL='http://api.example.com',
)
@mock.patch('wagtail.contrib.wagtailfrontendcache.backends.HTTPBackend.purge')
class TestDocumentCacheInvalidation(TestCase):
    fixtures = ['demosite.json']

    @classmethod
    def setUpClass(cls):
        super(TestDocumentCacheInvalidation, cls).setUpClass()
        signal_handlers.register_signal_handlers()

    @classmethod
    def tearDownClass(cls):
        super(TestDocumentCacheInvalidation, cls).tearDownClass()
        signal_handlers.unregister_signal_handlers()

    def test_resave_document_purges(self, purge):
        get_document_model().objects.get(id=5).save()

        purge.assert_any_call('http://api.example.com/api/v1/documents/5/')

    def test_delete_document_purges(self, purge):
        get_document_model().objects.get(id=5).delete()

        purge.assert_any_call('http://api.example.com/api/v1/documents/5/')
