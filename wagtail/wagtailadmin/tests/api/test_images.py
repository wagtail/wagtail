import json

from django.test.utils import override_settings
from django.core.urlresolvers import reverse

from wagtail.wagtailimages.models import get_image_model

from .utils import AdminAPITestCase


class TestImageListing(AdminAPITestCase):
    fixtures = ['demosite.json']

    def get_response(self, **params):
        return self.client.get(reverse('wagtailadmin_api_v1:images:listing'), params)

    def get_image_id_list(self, content):
        return [image['id'] for image in content['results']]


    # BASIC TESTS

    def test_basic(self):
        response = self.get_response()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-type'], 'application/json')

        # Will crash if the JSON is invalid
        content = json.loads(response.content.decode('UTF-8'))

        # Check that the total count is there and correct
        self.assertIn('total_count', content)
        self.assertIsInstance(content['total_count'], int)
        self.assertEqual(content['total_count'], get_image_model().objects.count())

        # Check that the results section is there
        self.assertIn('results', content)
        self.assertIsInstance(content['results'], list)

        # Check that each image has a meta section with type and detail_url attributes
        for image in content['results']:
            self.assertIn('meta', image)
            self.assertIsInstance(image['meta'], dict)
            self.assertEqual(set(image['meta'].keys()), {'type', 'detail_url'})

            # Type should always be wagtailimages.Image
            self.assertEqual(image['meta']['type'], 'wagtailimages.Image')

            # Check detail url
            self.assertEqual(image['meta']['detail_url'], 'http://localhost/admin/api/v1beta/images/%d/' % image['id'])


    #  FIELDS

    def test_fields_default(self):
        response = self.get_response()
        content = json.loads(response.content.decode('UTF-8'))

        for image in content['results']:
            self.assertEqual(set(image.keys()), {'id', 'meta', 'title', 'width', 'height', 'tags'})

    def test_fields(self):
        response = self.get_response(fields='title,width,height')
        content = json.loads(response.content.decode('UTF-8'))

        for image in content['results']:
            self.assertEqual(set(image.keys()), {'id', 'meta', 'title', 'width', 'height'})

    def test_fields_tags(self):
        response = self.get_response(fields='tags')
        content = json.loads(response.content.decode('UTF-8'))

        for image in content['results']:
            self.assertEqual(set(image.keys()), {'id', 'meta', 'tags'})
            self.assertIsInstance(image['tags'], list)

    def test_fields_which_are_not_in_api_fields_gives_error(self):
        response = self.get_response(fields='uploaded_by_user')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "unknown fields: uploaded_by_user"})

    def test_fields_unknown_field_gives_error(self):
        response = self.get_response(fields='123,title,abc')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "unknown fields: 123, abc"})


    # FILTERING

    def test_filtering_exact_filter(self):
        response = self.get_response(title='James Joyce')
        content = json.loads(response.content.decode('UTF-8'))

        image_id_list = self.get_image_id_list(content)
        self.assertEqual(image_id_list, [5])

    def test_filtering_on_id(self):
        response = self.get_response(id=10)
        content = json.loads(response.content.decode('UTF-8'))

        image_id_list = self.get_image_id_list(content)
        self.assertEqual(image_id_list, [10])

    def test_filtering_tags(self):
        get_image_model().objects.get(id=6).tags.add('test')

        response = self.get_response(tags='test')
        content = json.loads(response.content.decode('UTF-8'))

        image_id_list = self.get_image_id_list(content)
        self.assertEqual(image_id_list, [6])

    def test_filtering_unknown_field_gives_error(self):
        response = self.get_response(not_a_field='abc')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "query parameter is not an operation or a recognised field: not_a_field"})


    # ORDERING

    def test_ordering_by_title(self):
        response = self.get_response(order='title')
        content = json.loads(response.content.decode('UTF-8'))

        image_id_list = self.get_image_id_list(content)
        self.assertEqual(image_id_list, [6, 15, 13, 5, 10, 11, 8, 7, 4, 14, 12, 9])

    def test_ordering_by_title_backwards(self):
        response = self.get_response(order='-title')
        content = json.loads(response.content.decode('UTF-8'))

        image_id_list = self.get_image_id_list(content)
        self.assertEqual(image_id_list, [9, 12, 14, 4, 7, 8, 11, 10, 5, 13, 15, 6])

    def test_ordering_by_random(self):
        response_1 = self.get_response(order='random')
        content_1 = json.loads(response_1.content.decode('UTF-8'))
        image_id_list_1 = self.get_image_id_list(content_1)

        response_2 = self.get_response(order='random')
        content_2 = json.loads(response_2.content.decode('UTF-8'))
        image_id_list_2 = self.get_image_id_list(content_2)

        self.assertNotEqual(image_id_list_1, image_id_list_2)

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

        self.assertEqual(len(content['results']), 2)

    def test_limit_total_count(self):
        response = self.get_response(limit=2)
        content = json.loads(response.content.decode('UTF-8'))

        # The total count must not be affected by "limit"
        self.assertEqual(content['total_count'], get_image_model().objects.count())

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

        self.assertEqual(len(content['results']), 2)


    # OFFSET

    def test_offset_10_usually_appears_7th_in_list(self):
        response = self.get_response()
        content = json.loads(response.content.decode('UTF-8'))
        image_id_list = self.get_image_id_list(content)
        self.assertEqual(image_id_list.index(10), 6)

    def test_offset_10_moves_after_offset(self):
        response = self.get_response(offset=4)
        content = json.loads(response.content.decode('UTF-8'))
        image_id_list = self.get_image_id_list(content)
        self.assertEqual(image_id_list.index(10), 2)

    def test_offset_total_count(self):
        response = self.get_response(offset=10)
        content = json.loads(response.content.decode('UTF-8'))

        # The total count must not be affected by "offset"
        self.assertEqual(content['total_count'], get_image_model().objects.count())

    def test_offset_not_integer_gives_error(self):
        response = self.get_response(offset='abc')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "offset must be a positive integer"})


    # SEARCH

    def test_search_for_james_joyce(self):
        response = self.get_response(search='james')
        content = json.loads(response.content.decode('UTF-8'))

        image_id_list = self.get_image_id_list(content)

        self.assertEqual(set(image_id_list), set([5]))

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


class TestImageDetail(AdminAPITestCase):
    fixtures = ['demosite.json']

    def get_response(self, image_id, **params):
        return self.client.get(reverse('wagtailadmin_api_v1:images:detail', args=(image_id, )), params)


    def test_basic(self):
        response = self.get_response(5)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-type'], 'application/json')

        # Will crash if the JSON is invalid
        content = json.loads(response.content.decode('UTF-8'))

        # Check the id field
        self.assertIn('id', content)
        self.assertEqual(content['id'], 5)

        # Check that the meta section is there
        self.assertIn('meta', content)
        self.assertIsInstance(content['meta'], dict)

        # Check the meta type
        self.assertIn('type', content['meta'])
        self.assertEqual(content['meta']['type'], 'wagtailimages.Image')

        # Check the meta detail_url
        self.assertIn('detail_url', content['meta'])
        self.assertEqual(content['meta']['detail_url'], 'http://localhost/admin/api/v1beta/images/5/')

        # Check the title field
        self.assertIn('title', content)
        self.assertEqual(content['title'], "James Joyce")

        # Check the width and height fields
        self.assertIn('width', content)
        self.assertIn('height', content)
        self.assertEqual(content['width'], 500)
        self.assertEqual(content['height'], 392)

        # Check the tags field
        self.assertIn('tags', content)
        self.assertEqual(content['tags'], [])

    def test_tags(self):
        image = get_image_model().objects.get(id=5)
        image.tags.add('hello')
        image.tags.add('world')

        response = self.get_response(5)
        content = json.loads(response.content.decode('UTF-8'))

        self.assertIn('tags', content)
        self.assertEqual(content['tags'], ['hello', 'world'])
