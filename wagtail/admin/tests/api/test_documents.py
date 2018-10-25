import json

from django.urls import reverse

from wagtail.api.v2.tests.test_documents import TestDocumentDetail, TestDocumentListing
from wagtail.documents.models import Document

from .utils import AdminAPITestCase


class TestAdminDocumentListing(AdminAPITestCase, TestDocumentListing):
    fixtures = ['demosite.json']

    def get_response(self, **params):
        return self.client.get(reverse('wagtailadmin_api_v1:documents:listing'), params)

    def get_document_id_list(self, content):
        return [document['id'] for document in content['items']]

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
        self.assertEqual(content['meta']['total_count'], Document.objects.count())

        # Check that the items section is there
        self.assertIn('items', content)
        self.assertIsInstance(content['items'], list)

        # Check that each document has a meta section with type, detail_url and tags attributes
        for document in content['items']:
            self.assertIn('meta', document)
            self.assertIsInstance(document['meta'], dict)
            self.assertEqual(set(document['meta'].keys()), {'type', 'detail_url', 'download_url', 'tags'})

            # Type should always be wagtaildocs.Document
            self.assertEqual(document['meta']['type'], 'wagtaildocs.Document')

            # Check detail_url
            self.assertEqual(document['meta']['detail_url'], 'http://localhost/admin/api/v2beta/documents/%d/' % document['id'])

            # Check download_url
            self.assertTrue(document['meta']['download_url'].startswith('http://localhost/documents/%d/' % document['id']))

    # FIELDS

    def test_fields_default(self):
        response = self.get_response()
        content = json.loads(response.content.decode('UTF-8'))

        for document in content['items']:
            self.assertEqual(set(document.keys()), {'id', 'meta', 'title'})
            self.assertEqual(set(document['meta'].keys()), {'type', 'detail_url', 'download_url', 'tags'})


class TestAdminDocumentDetail(AdminAPITestCase, TestDocumentDetail):
    fixtures = ['demosite.json']

    def get_response(self, image_id, **params):
        return self.client.get(reverse('wagtailadmin_api_v1:documents:detail', args=(image_id, )), params)

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
        self.assertEqual(content['meta']['detail_url'], 'http://localhost/admin/api/v2beta/documents/1/')

        # Check the meta download_url
        self.assertIn('download_url', content['meta'])
        self.assertEqual(content['meta']['download_url'], 'http://localhost/documents/1/wagtail_by_markyharky.jpg')

        # Check the title field
        self.assertIn('title', content)
        self.assertEqual(content['title'], "Wagtail by mark Harkin")

        # Check the tags field
        self.assertIn('tags', content['meta'])
        self.assertEqual(content['meta']['tags'], [])
