from __future__ import absolute_import, unicode_literals

import collections
import json

import mock
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from wagtail.contrib.wagtailapi import signal_handlers
from wagtail.tests.demosite import models
from wagtail.tests.testapp.models import StreamPage
from wagtail.wagtailcore.models import Page


def get_total_page_count():
    # Need to take away 1 as the root page is invisible over the API
    return Page.objects.live().public().count() - 1


class TestPageListing(TestCase):
    fixtures = ['demosite.json']

    def get_response(self, **params):
        return self.client.get(reverse('wagtailapi_v1:pages:listing'), params)

    def get_page_id_list(self, content):
        return [page['id'] for page in content['pages']]


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
        self.assertEqual(content['meta']['total_count'], get_total_page_count())

        # Check that the pages section is there
        self.assertIn('pages', content)
        self.assertIsInstance(content['pages'], list)

        # Check that each page has a meta section with type and detail_url attributes
        for page in content['pages']:
            self.assertIn('meta', page)
            self.assertIsInstance(page['meta'], dict)
            self.assertEqual(set(page['meta'].keys()), {'type', 'detail_url'})

    def test_unpublished_pages_dont_appear_in_list(self):
        total_count = get_total_page_count()

        page = models.BlogEntryPage.objects.get(id=16)
        page.unpublish()

        response = self.get_response()
        content = json.loads(response.content.decode('UTF-8'))
        self.assertEqual(content['meta']['total_count'], total_count - 1)

    def test_private_pages_dont_appear_in_list(self):
        total_count = get_total_page_count()

        page = models.BlogIndexPage.objects.get(id=5)
        page.view_restrictions.create(password='test')

        new_total_count = get_total_page_count()
        self.assertNotEqual(total_count, new_total_count)

        response = self.get_response()
        content = json.loads(response.content.decode('UTF-8'))
        self.assertEqual(content['meta']['total_count'], new_total_count)


    # TYPE FILTER

    def test_type_filter_results_are_all_blog_entries(self):
        response = self.get_response(type='demosite.BlogEntryPage')
        content = json.loads(response.content.decode('UTF-8'))

        for page in content['pages']:
            self.assertEqual(page['meta']['type'], 'demosite.BlogEntryPage')

    def test_type_filter_total_count(self):
        response = self.get_response(type='demosite.BlogEntryPage')
        content = json.loads(response.content.decode('UTF-8'))

        # Total count must be reduced as this filters the results
        self.assertEqual(content['meta']['total_count'], 3)

    def test_non_existant_type_gives_error(self):
        response = self.get_response(type='demosite.IDontExist')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "type doesn't exist"})

    def test_non_page_type_gives_error(self):
        response = self.get_response(type='auth.User')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "type doesn't exist"})

    # EXTRA FIELDS

    def test_extra_fields_default(self):
        response = self.get_response(type='demosite.BlogEntryPage')
        content = json.loads(response.content.decode('UTF-8'))

        for page in content['pages']:
            self.assertEqual(set(page.keys()), {'id', 'meta', 'title'})

    def test_extra_fields(self):
        response = self.get_response(type='demosite.BlogEntryPage', fields='title,date,feed_image')
        content = json.loads(response.content.decode('UTF-8'))

        for page in content['pages']:
            self.assertEqual(set(page.keys()), {'id', 'meta', 'title', 'date', 'feed_image'})

    def test_extra_fields_child_relation(self):
        response = self.get_response(type='demosite.BlogEntryPage', fields='title,related_links')
        content = json.loads(response.content.decode('UTF-8'))

        for page in content['pages']:
            self.assertEqual(set(page.keys()), {'id', 'meta', 'title', 'related_links'})
            self.assertIsInstance(page['related_links'], list)

    def test_extra_fields_foreign_key(self):
        response = self.get_response(type='demosite.BlogEntryPage', fields='title,date,feed_image')
        content = json.loads(response.content.decode('UTF-8'))

        for page in content['pages']:
            feed_image = page['feed_image']

            if feed_image is not None:
                self.assertIsInstance(feed_image, dict)
                self.assertEqual(set(feed_image.keys()), {'id', 'meta'})
                self.assertIsInstance(feed_image['id'], int)
                self.assertIsInstance(feed_image['meta'], dict)
                self.assertEqual(set(feed_image['meta'].keys()), {'type', 'detail_url'})
                self.assertEqual(feed_image['meta']['type'], 'wagtailimages.Image')
                self.assertEqual(
                    feed_image['meta']['detail_url'], 'http://localhost/api/v1/images/%d/' % feed_image['id']
                )

    def test_extra_fields_tags(self):
        response = self.get_response(type='demosite.BlogEntryPage', fields='tags')
        content = json.loads(response.content.decode('UTF-8'))

        for page in content['pages']:
            self.assertEqual(set(page.keys()), {'id', 'meta', 'tags'})
            self.assertIsInstance(page['tags'], list)

    def test_extra_field_ordering(self):
        response = self.get_response(type='demosite.BlogEntryPage', fields='date,title,feed_image,related_links')

        # Will crash if the JSON is invalid
        content = json.loads(response.content.decode('UTF-8'))

        # Test field order
        content = json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode(response.content.decode('UTF-8'))
        field_order = [
            'id',
            'meta',
            'title',
            'date',
            'feed_image',
            'related_links',
        ]
        self.assertEqual(list(content['pages'][0].keys()), field_order)

    def test_extra_fields_without_type_gives_error(self):
        response = self.get_response(fields='title,related_links')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "unknown fields: related_links"})

    def test_extra_fields_which_are_not_in_api_fields_gives_error(self):
        response = self.get_response(fields='path')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "unknown fields: path"})

    def test_extra_fields_unknown_field_gives_error(self):
        response = self.get_response(fields='123,title,abc')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "unknown fields: 123, abc"})


    # FILTERING

    def test_filtering_exact_filter(self):
        response = self.get_response(title='Home page')
        content = json.loads(response.content.decode('UTF-8'))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [2])

    def test_filtering_exact_filter_on_specific_field(self):
        response = self.get_response(type='demosite.BlogEntryPage', date='2013-12-02')
        content = json.loads(response.content.decode('UTF-8'))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [16])

    def test_filtering_on_id(self):
        response = self.get_response(id=16)
        content = json.loads(response.content.decode('UTF-8'))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [16])

    def test_filtering_doesnt_work_on_specific_fields_without_type(self):
        response = self.get_response(date='2013-12-02')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "query parameter is not an operation or a recognised field: date"})

    def test_filtering_tags(self):
        response = self.get_response(type='demosite.BlogEntryPage', tags='wagtail')
        content = json.loads(response.content.decode('UTF-8'))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [16, 18])

    def test_filtering_multiple_tags(self):
        response = self.get_response(type='demosite.BlogEntryPage', tags='wagtail,bird')
        content = json.loads(response.content.decode('UTF-8'))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [16])

    def test_filtering_unknown_field_gives_error(self):
        response = self.get_response(not_a_field='abc')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "query parameter is not an operation or a recognised field: not_a_field"})


    # CHILD OF FILTER

    def test_child_of_filter(self):
        response = self.get_response(child_of=5)
        content = json.loads(response.content.decode('UTF-8'))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [16, 18, 19])

    def test_child_of_with_type(self):
        response = self.get_response(type='demosite.EventPage', child_of=5)
        content = json.loads(response.content.decode('UTF-8'))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [])

    def test_child_of_unknown_page_gives_error(self):
        response = self.get_response(child_of=1000)
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "parent page doesn't exist"})

    def test_child_of_not_integer_gives_error(self):
        response = self.get_response(child_of='abc')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "child_of must be a positive integer"})

    def test_child_of_page_thats_not_in_same_site_gives_error(self):
        # Root page is not in any site, so pretend it doesn't exist
        response = self.get_response(child_of=1)
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "parent page doesn't exist"})


    # DESCENDANT OF FILTER

    def test_descendant_of_filter(self):
        response = self.get_response(descendant_of=6)
        content = json.loads(response.content.decode('UTF-8'))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [10, 15, 17, 21, 22, 23])

    def test_descendant_of_with_type(self):
        response = self.get_response(type='tests.EventPage', descendant_of=6)
        content = json.loads(response.content.decode('UTF-8'))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [])

    def test_descendant_of_unknown_page_gives_error(self):
        response = self.get_response(descendant_of=1000)
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "ancestor page doesn't exist"})

    def test_descendant_of_not_integer_gives_error(self):
        response = self.get_response(descendant_of='abc')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "descendant_of must be a positive integer"})

    def test_descendant_of_page_thats_not_in_same_site_gives_error(self):
        # Root page is not in any site, so pretend it doesn't exist
        response = self.get_response(descendant_of=1)
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "ancestor page doesn't exist"})

    def test_descendant_of_when_filtering_by_child_of_gives_error(self):
        response = self.get_response(descendant_of=6, child_of=5)
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "filtering by descendant_of with child_of is not supported"})


    # ORDERING

    def test_ordering_default(self):
        response = self.get_response()
        content = json.loads(response.content.decode('UTF-8'))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [2, 4, 8, 9, 5, 16, 18, 19, 6, 10, 15, 17, 21, 22, 23, 20, 13, 14, 12])

    def test_ordering_by_title(self):
        response = self.get_response(order='title')
        content = json.loads(response.content.decode('UTF-8'))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [21, 22, 19, 23, 5, 16, 18, 12, 14, 8, 9, 4, 2, 13, 20, 17, 6, 10, 15])

    def test_ordering_by_title_backwards(self):
        response = self.get_response(order='-title')
        content = json.loads(response.content.decode('UTF-8'))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [15, 10, 6, 17, 20, 13, 2, 4, 9, 8, 14, 12, 18, 16, 5, 23, 19, 22, 21])

    def test_ordering_by_random(self):
        response_1 = self.get_response(order='random')
        content_1 = json.loads(response_1.content.decode('UTF-8'))
        page_id_list_1 = self.get_page_id_list(content_1)

        response_2 = self.get_response(order='random')
        content_2 = json.loads(response_2.content.decode('UTF-8'))
        page_id_list_2 = self.get_page_id_list(content_2)

        self.assertNotEqual(page_id_list_1, page_id_list_2)

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

    def test_ordering_default_with_type(self):
        response = self.get_response(type='demosite.BlogEntryPage')
        content = json.loads(response.content.decode('UTF-8'))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [16, 18, 19])

    def test_ordering_by_title_with_type(self):
        response = self.get_response(type='demosite.BlogEntryPage', order='title')
        content = json.loads(response.content.decode('UTF-8'))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [19, 16, 18])

    def test_ordering_by_specific_field_with_type(self):
        response = self.get_response(type='demosite.BlogEntryPage', order='date')
        content = json.loads(response.content.decode('UTF-8'))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [16, 18, 19])

    def test_ordering_by_unknown_field_gives_error(self):
        response = self.get_response(order='not_a_field')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "cannot order by 'not_a_field' (unknown field)"})


    # LIMIT

    def test_limit_only_two_results_returned(self):
        response = self.get_response(limit=2)
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(len(content['pages']), 2)

    def test_limit_total_count(self):
        response = self.get_response(limit=2)
        content = json.loads(response.content.decode('UTF-8'))

        # The total count must not be affected by "limit"
        self.assertEqual(content['meta']['total_count'], get_total_page_count())

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

        self.assertEqual(len(content['pages']), 2)


    # OFFSET

    def test_offset_5_usually_appears_5th_in_list(self):
        response = self.get_response()
        content = json.loads(response.content.decode('UTF-8'))
        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list.index(5), 4)

    def test_offset_5_moves_after_offset(self):
        response = self.get_response(offset=4)
        content = json.loads(response.content.decode('UTF-8'))
        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list.index(5), 0)

    def test_offset_total_count(self):
        response = self.get_response(offset=10)
        content = json.loads(response.content.decode('UTF-8'))

        # The total count must not be affected by "offset"
        self.assertEqual(content['meta']['total_count'], get_total_page_count())

    def test_offset_not_integer_gives_error(self):
        response = self.get_response(offset='abc')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "offset must be a positive integer"})


    # SEARCH

    def test_search_for_blog(self):
        response = self.get_response(search='blog')
        content = json.loads(response.content.decode('UTF-8'))

        page_id_list = self.get_page_id_list(content)

        # Check that the results are the blog index and three blog pages
        self.assertEqual(set(page_id_list), set([5, 16, 18, 19]))

    def test_search_with_type(self):
        response = self.get_response(type='demosite.BlogEntryPage', search='blog')
        content = json.loads(response.content.decode('UTF-8'))

        page_id_list = self.get_page_id_list(content)

        self.assertEqual(set(page_id_list), set([16, 18, 19]))

    def test_search_when_ordering_gives_error(self):
        response = self.get_response(search='blog', order='title')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "ordering with a search query is not supported"})

    @override_settings(WAGTAILAPI_SEARCH_ENABLED=False)
    def test_search_when_disabled_gives_error(self):
        response = self.get_response(search='blog')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "search is disabled"})

    def test_search_when_filtering_by_tag_gives_error(self):
        response = self.get_response(type='demosite.BlogEntryPage', search='blog', tags='wagtail')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "filtering by tag with a search query is not supported"})


class TestPageDetail(TestCase):
    fixtures = ['demosite.json']

    def get_response(self, page_id, **params):
        return self.client.get(reverse('wagtailapi_v1:pages:detail', args=(page_id, )), params)

    def test_basic(self):
        response = self.get_response(16)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-type'], 'application/json')

        # Will crash if the JSON is invalid
        content = json.loads(response.content.decode('UTF-8'))

        # Check the id field
        self.assertIn('id', content)
        self.assertEqual(content['id'], 16)

        # Check that the meta section is there
        self.assertIn('meta', content)
        self.assertIsInstance(content['meta'], dict)

        # Check the meta type
        self.assertIn('type', content['meta'])
        self.assertEqual(content['meta']['type'], 'demosite.BlogEntryPage')

        # Check the meta detail_url
        self.assertIn('detail_url', content['meta'])
        self.assertEqual(content['meta']['detail_url'], 'http://localhost/api/v1/pages/16/')

        # Check the parent field
        self.assertIn('parent', content)
        self.assertIsInstance(content['parent'], dict)
        self.assertEqual(set(content['parent'].keys()), {'id', 'meta'})
        self.assertEqual(content['parent']['id'], 5)
        self.assertIsInstance(content['parent']['meta'], dict)
        self.assertEqual(set(content['parent']['meta'].keys()), {'type', 'detail_url'})
        self.assertEqual(content['parent']['meta']['type'], 'demosite.BlogIndexPage')
        self.assertEqual(content['parent']['meta']['detail_url'], 'http://localhost/api/v1/pages/5/')

        # Check that the custom fields are included
        self.assertIn('date', content)
        self.assertIn('body', content)
        self.assertIn('tags', content)
        self.assertIn('feed_image', content)
        self.assertIn('related_links', content)
        self.assertIn('carousel_items', content)

        # Check that the date was serialised properly
        self.assertEqual(content['date'], '2013-12-02')

        # Check that the tags were serialised properly
        self.assertEqual(content['tags'], ['bird', 'wagtail'])

        # Check that the feed image was serialised properly
        self.assertIsInstance(content['feed_image'], dict)
        self.assertEqual(set(content['feed_image'].keys()), {'id', 'meta'})
        self.assertEqual(content['feed_image']['id'], 7)
        self.assertIsInstance(content['feed_image']['meta'], dict)
        self.assertEqual(set(content['feed_image']['meta'].keys()), {'type', 'detail_url'})
        self.assertEqual(content['feed_image']['meta']['type'], 'wagtailimages.Image')
        self.assertEqual(content['feed_image']['meta']['detail_url'], 'http://localhost/api/v1/images/7/')

        # Check that the child relations were serialised properly
        self.assertEqual(content['related_links'], [])
        for carousel_item in content['carousel_items']:
            self.assertEqual(set(carousel_item.keys()), {'embed_url', 'link', 'caption', 'image'})

    def test_meta_parent_id_doesnt_show_root_page(self):
        # Root page isn't in the site so don't show it if the user is looking at the home page
        response = self.get_response(2)
        content = json.loads(response.content.decode('UTF-8'))

        self.assertNotIn('parent', content['meta'])

    def test_field_ordering(self):
        response = self.get_response(16)

        # Will crash if the JSON is invalid
        content = json.loads(response.content.decode('UTF-8'))

        # Test field order
        content = json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode(response.content.decode('UTF-8'))
        field_order = [
            'id',
            'meta',
            'parent',
            'title',
            'body',
            'tags',
            'date',
            'feed_image',
            'carousel_items',
            'related_links',
        ]
        self.assertEqual(list(content.keys()), field_order)

    def test_null_foreign_key(self):
        models.BlogEntryPage.objects.filter(id=16).update(feed_image_id=None)

        response = self.get_response(16)
        content = json.loads(response.content.decode('UTF-8'))

        self.assertIn('related_links', content)
        self.assertEqual(content['feed_image'], None)


class TestPageDetailWithStreamField(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        self.homepage = Page.objects.get(url_path='/home/')

    def make_stream_page(self, body):
        stream_page = StreamPage(
            title='stream page',
            body=body
        )
        return self.homepage.add_child(instance=stream_page)

    def test_can_fetch_streamfield_content(self):
        stream_page = self.make_stream_page('[{"type": "text", "value": "foo"}]')

        response_url = reverse('wagtailapi_v1:pages:detail', args=(stream_page.id, ))
        response = self.client.get(response_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')

        content = json.loads(response.content.decode('utf-8'))

        self.assertIn('id', content)
        self.assertEqual(content['id'], stream_page.id)
        self.assertIn('body', content)
        self.assertEqual(content['body'], [{'type': 'text', 'value': 'foo'}])

    def test_image_block(self):
        stream_page = self.make_stream_page('[{"type": "image", "value": 1}]')

        response_url = reverse('wagtailapi_v1:pages:detail', args=(stream_page.id, ))
        response = self.client.get(response_url)
        content = json.loads(response.content.decode('utf-8'))

        # ForeignKeys in a StreamField shouldn't be translated into dictionary representation
        self.assertEqual(content['body'], [{'type': 'image', 'value': 1}])


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
class TestPageCacheInvalidation(TestCase):
    fixtures = ['demosite.json']

    @classmethod
    def setUpClass(cls):
        super(TestPageCacheInvalidation, cls).setUpClass()
        signal_handlers.register_signal_handlers()

    @classmethod
    def tearDownClass(cls):
        super(TestPageCacheInvalidation, cls).tearDownClass()
        signal_handlers.unregister_signal_handlers()

    def test_republish_page_purges(self, purge):
        Page.objects.get(id=2).save_revision().publish()

        purge.assert_any_call('http://api.example.com/api/v1/pages/2/')

    def test_unpublish_page_purges(self, purge):
        Page.objects.get(id=2).unpublish()

        purge.assert_any_call('http://api.example.com/api/v1/pages/2/')

    def test_delete_page_purges(self, purge):
        Page.objects.get(id=16).delete()

        purge.assert_any_call('http://api.example.com/api/v1/pages/16/')

    def test_save_draft_doesnt_purge(self, purge):
        Page.objects.get(id=2).save_revision()

        purge.assert_not_called()
