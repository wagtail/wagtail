from __future__ import absolute_import, unicode_literals

import json

from django.core.urlresolvers import reverse

from wagtail.api.v3.tests.test_images import TestImageDetail, TestImageListing
from wagtail.wagtailimages import get_image_model
from wagtail.wagtailimages.tests.utils import get_test_image_file

from .utils import AdminAPITestCase


class TestAdminImageListing(AdminAPITestCase, TestImageListing):
    fixtures = ['demosite.json']

    def get_response(self, **params):
        return self.client.get(reverse('wagtailadmin_api:images:listing'), params)

    def get_image_id_list(self, content):
        return [image['meta']['id'] for image in content['items']]


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
        self.assertEqual(content['meta']['total_count'], get_image_model().objects.count())

        # Check that the items section is there
        self.assertIn('items', content)
        self.assertIsInstance(content['items'], list)

        # Check that each image has a meta section with type, detail_url and tags attributes
        for image in content['items']:
            self.assertIn('meta', image)
            self.assertIsInstance(image['meta'], dict)
            self.assertEqual(set(image['meta'].keys()), {'id', 'type', 'detail_url'})

            # Type should always be wagtailimages.Image
            self.assertEqual(image['meta']['type'], 'wagtailimages.Image')

            # Check detail url
            self.assertEqual(image['meta']['detail_url'], 'http://localhost/admin/api/v3beta/images/%d/' % image['meta']['id'])


    #  FIELDS

    def test_fields_default(self):
        response = self.get_response()
        content = json.loads(response.content.decode('UTF-8'))

        for image in content['items']:
            self.assertEqual(set(image.keys()), {'meta', 'title', 'tags', 'width', 'height', 'thumbnail'})
            self.assertEqual(set(image['meta'].keys()), {'id', 'type', 'detail_url'})

    def test_fields(self):
        response = self.get_response(fields='width,height')
        content = json.loads(response.content.decode('UTF-8'))

        for image in content['items']:
            self.assertEqual(set(image.keys()), {'meta', 'title', 'tags', 'width', 'height', 'thumbnail'})
            self.assertEqual(set(image['meta'].keys()), {'id', 'type', 'detail_url'})

    def test_remove_fields(self):
        response = self.get_response(fields='-title')
        content = json.loads(response.content.decode('UTF-8'))

        for image in content['items']:
            self.assertEqual(set(image.keys()), {'meta', 'tags', 'width', 'height', 'thumbnail'})

    def test_remove_meta_fields(self):
        response = self.get_response(fields='-type')
        content = json.loads(response.content.decode('UTF-8'))

        for image in content['items']:
            self.assertEqual(set(image.keys()), {'meta', 'tags', 'title', 'width', 'height', 'thumbnail'})
            self.assertEqual(set(image['meta'].keys()), {'id', 'detail_url'})

    def test_remove_all_meta_fields(self):
        response = self.get_response(fields='-id,-type,-detail_url')
        content = json.loads(response.content.decode('UTF-8'))

        for image in content['items']:
            self.assertEqual(set(image.keys()), {'title', 'tags', 'width', 'height', 'thumbnail'})

    def test_all_fields(self):
        response = self.get_response(fields='*')
        content = json.loads(response.content.decode('UTF-8'))

        for image in content['items']:
            self.assertEqual(set(image.keys()), {'meta', 'title', 'tags', 'width', 'height', 'thumbnail'})
            self.assertEqual(set(image['meta'].keys()), {'id', 'type', 'detail_url'})

    def test_all_fields_then_remove_something(self):
        response = self.get_response(fields='*,-title,-tags,-type')
        content = json.loads(response.content.decode('UTF-8'))

        for image in content['items']:
            self.assertEqual(set(image.keys()), {'meta', 'width', 'height', 'thumbnail'})
            self.assertEqual(set(image['meta'].keys()), {'id', 'detail_url'})

    def test_fields_tags(self):
        response = self.get_response(fields='tags')
        content = json.loads(response.content.decode('UTF-8'))

        for image in content['items']:
            self.assertIsInstance(image['tags'], list)


class TestAdminImageDetail(AdminAPITestCase, TestImageDetail):
    fixtures = ['demosite.json']

    def get_response(self, image_id, **params):
        return self.client.get(reverse('wagtailadmin_api:images:detail', args=(image_id, )), params)

    def test_basic(self):
        response = self.get_response(5)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-type'], 'application/json')

        # Will crash if the JSON is invalid
        content = json.loads(response.content.decode('UTF-8'))

        # Check that the meta section is there
        self.assertIsInstance(content['meta'], dict)

        # Check the id field
        self.assertEqual(content['meta']['id'], 5)

        # Check the meta type
        self.assertEqual(content['meta']['type'], 'wagtailimages.Image')

        # Check the meta detail_url
        self.assertEqual(content['meta']['detail_url'], 'http://localhost/admin/api/v3beta/images/5/')

        # Check the thumbnail

        # Note: This is None because the source image doesn't exist
        #       See test_thumbnail below for working example
        self.assertEqual(content['thumbnail'], {'error': 'SourceImageIOError'})

        # Check the title field
        self.assertEqual(content['title'], "James Joyce")

        # Check the tags field
        self.assertEqual(content['tags'], [])

        # Check the width and height fields
        self.assertEqual(content['width'], 500)
        self.assertEqual(content['height'], 392)

    def test_thumbnail(self):
        # Add a new image with source file
        image = get_image_model().objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

        response = self.get_response(image.id)
        content = json.loads(response.content.decode('UTF-8'))

        self.assertIn('thumbnail', content)
        self.assertEqual(content['thumbnail']['width'], 165)
        self.assertEqual(content['thumbnail']['height'], 123)
        self.assertTrue(content['thumbnail']['url'].startswith('/media/images/test'))

        # Check that source_image_error didn't appear
        self.assertNotIn('source_image_error', content['meta'])
