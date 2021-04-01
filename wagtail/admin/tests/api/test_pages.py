import collections
import datetime
import json

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from wagtail.api.v2.tests.test_pages import TestPageDetail, TestPageListing
from wagtail.core import hooks
from wagtail.core.models import Locale, Page
from wagtail.tests.demosite import models
from wagtail.tests.testapp.models import SimplePage, StreamPage
from wagtail.users.models import UserProfile

from .utils import AdminAPITestCase


def get_total_page_count():
    # Need to take away 1 as the root page is invisible over the API by default
    return Page.objects.count() - 1


class TestAdminPageListing(AdminAPITestCase, TestPageListing):
    fixtures = ['demosite.json']

    def get_response(self, **params):
        return self.client.get(reverse('wagtailadmin_api:pages:listing'), params)

    def get_page_id_list(self, content):
        return [page['id'] for page in content['items']]

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

        # Check that the items section is there
        self.assertIn('items', content)
        self.assertIsInstance(content['items'], list)

        # Check that each page has a meta section with type, detail_url, html_url, status and children attributes
        for page in content['items']:
            self.assertIn('meta', page)
            self.assertIsInstance(page['meta'], dict)
            self.assertEqual(set(page['meta'].keys()), {'type', 'detail_url', 'html_url', 'status', 'children', 'slug', 'first_published_at', 'latest_revision_created_at'})

        # Check the type info
        self.assertIsInstance(content['__types'], dict)
        self.assertEqual(set(content['__types'].keys()), {
            'demosite.EventPage',
            'demosite.StandardIndexPage',
            'demosite.PersonPage',
            'demosite.HomePage',
            'demosite.StandardPage',
            'demosite.EventIndexPage',
            'demosite.ContactPage',
            'demosite.BlogEntryPage',
            'demosite.BlogIndexPage',
        })
        self.assertEqual(set(content['__types']['demosite.EventPage'].keys()), {'verbose_name', 'verbose_name_plural'})
        self.assertEqual(content['__types']['demosite.EventPage']['verbose_name'], 'event page')
        self.assertEqual(content['__types']['demosite.EventPage']['verbose_name_plural'], 'event pages')

    # Not applicable to the admin API
    test_unpublished_pages_dont_appear_in_list = None
    test_private_pages_dont_appear_in_list = None

    def test_unpublished_pages_appear_in_list(self):
        total_count = get_total_page_count()

        page = models.BlogEntryPage.objects.get(id=16)
        page.unpublish()

        response = self.get_response()
        content = json.loads(response.content.decode('UTF-8'))
        self.assertEqual(content['meta']['total_count'], total_count)

    def test_private_pages_appear_in_list(self):
        total_count = get_total_page_count()

        page = models.BlogIndexPage.objects.get(id=5)
        page.view_restrictions.create(password='test')

        new_total_count = get_total_page_count()
        self.assertEqual(total_count, total_count)

        response = self.get_response()
        content = json.loads(response.content.decode('UTF-8'))
        self.assertEqual(content['meta']['total_count'], new_total_count)

    def test_get_in_non_content_language(self):
        # set logged-in user's admin UI language to Swedish
        user = get_user_model().objects.get(email='test@email.com')
        UserProfile.objects.update_or_create(user=user, defaults={'preferred_language': 'se'})

        response = self.get_response()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-type'], 'application/json')

        # Will crash if the JSON is invalid
        content = json.loads(response.content.decode('UTF-8'))
        self.assertIn('meta', content)

    # FIELDS

    # Not applicable to the admin API
    test_parent_field_gives_error = None

    def test_fields(self):
        response = self.get_response(type='demosite.BlogEntryPage', fields='title,date,feed_image')
        content = json.loads(response.content.decode('UTF-8'))

        for page in content['items']:
            self.assertEqual(set(page.keys()), {'id', 'meta', 'title', 'admin_display_title', 'date', 'feed_image'})

    def test_fields_default(self):
        response = self.get_response(type='demosite.BlogEntryPage')
        content = json.loads(response.content.decode('UTF-8'))

        for page in content['items']:
            self.assertEqual(set(page.keys()), {'id', 'meta', 'title', 'admin_display_title'})
            self.assertEqual(set(page['meta'].keys()), {'type', 'detail_url', 'html_url', 'children', 'status', 'slug', 'first_published_at', 'latest_revision_created_at'})

    def test_remove_meta_fields(self):
        response = self.get_response(fields='-html_url')
        content = json.loads(response.content.decode('UTF-8'))

        for page in content['items']:
            self.assertEqual(set(page.keys()), {'id', 'meta', 'title', 'admin_display_title'})
            self.assertEqual(set(page['meta'].keys()), {'type', 'detail_url', 'slug', 'first_published_at', 'latest_revision_created_at', 'status', 'children'})

    def test_remove_all_meta_fields(self):
        response = self.get_response(fields='-type,-detail_url,-slug,-first_published_at,-html_url,-latest_revision_created_at,-status,-children')
        content = json.loads(response.content.decode('UTF-8'))

        for page in content['items']:
            self.assertEqual(set(page.keys()), {'id', 'title', 'admin_display_title'})

    def test_remove_fields(self):
        response = self.get_response(fields='-title,-admin_display_title')
        content = json.loads(response.content.decode('UTF-8'))

        for page in content['items']:
            self.assertEqual(set(page.keys()), {'id', 'meta'})

    def test_remove_id_field(self):
        response = self.get_response(fields='-id')
        content = json.loads(response.content.decode('UTF-8'))

        for page in content['items']:
            self.assertEqual(set(page.keys()), {'meta', 'title', 'admin_display_title'})

    def test_all_fields(self):
        response = self.get_response(type='demosite.BlogEntryPage', fields='*')
        content = json.loads(response.content.decode('UTF-8'))

        for page in content['items']:
            self.assertEqual(set(page.keys()), {'id', 'meta', 'title', 'admin_display_title', 'date', 'related_links', 'tags', 'carousel_items', 'body', 'feed_image', 'feed_image_thumbnail'})
            self.assertEqual(set(page['meta'].keys()), {'type', 'detail_url', 'show_in_menus', 'first_published_at', 'seo_title', 'slug', 'parent', 'html_url', 'search_description', 'locale', 'children', 'descendants', 'ancestors', 'translations', 'status', 'latest_revision_created_at'})

    def test_all_fields_then_remove_something(self):
        response = self.get_response(type='demosite.BlogEntryPage', fields='*,-title,-admin_display_title,-date,-seo_title,-status')
        content = json.loads(response.content.decode('UTF-8'))

        for page in content['items']:
            self.assertEqual(set(page.keys()), {'id', 'meta', 'related_links', 'tags', 'carousel_items', 'body', 'feed_image', 'feed_image_thumbnail'})
            self.assertEqual(set(page['meta'].keys()), {'type', 'detail_url', 'show_in_menus', 'first_published_at', 'slug', 'parent', 'html_url', 'search_description', 'locale', 'children', 'descendants', 'ancestors', 'translations', 'latest_revision_created_at'})

    def test_all_nested_fields(self):
        response = self.get_response(type='demosite.BlogEntryPage', fields='feed_image(*)')
        content = json.loads(response.content.decode('UTF-8'))

        for page in content['items']:
            self.assertEqual(set(page['feed_image'].keys()), {'id', 'meta', 'title', 'width', 'height', 'thumbnail'})

    def test_fields_foreign_key(self):
        # Only the base the detail_url is different here from the public API
        response = self.get_response(type='demosite.BlogEntryPage', fields='title,date,feed_image')
        content = json.loads(response.content.decode('UTF-8'))

        for page in content['items']:
            feed_image = page['feed_image']

            if feed_image is not None:
                self.assertIsInstance(feed_image, dict)
                self.assertEqual(set(feed_image.keys()), {'id', 'meta', 'title'})
                self.assertIsInstance(feed_image['id'], int)
                self.assertIsInstance(feed_image['meta'], dict)
                self.assertEqual(set(feed_image['meta'].keys()), {'type', 'detail_url', 'download_url'})
                self.assertEqual(feed_image['meta']['type'], 'wagtailimages.Image')
                self.assertEqual(feed_image['meta']['detail_url'], 'http://localhost/admin/api/main/images/%d/' % feed_image['id'])

    def test_fields_parent(self):
        response = self.get_response(type='demosite.BlogEntryPage', fields='parent')
        content = json.loads(response.content.decode('UTF-8'))

        for page in content['items']:
            parent = page['meta']['parent']

            # All blog entry pages have the same parent
            self.assertDictEqual(parent, {
                'id': 5,
                'meta': {
                    'type': 'demosite.BlogIndexPage',
                    'detail_url': 'http://localhost/admin/api/main/pages/5/',
                    'html_url': 'http://localhost/blog-index/',
                },
                'title': "Blog index"
            })

    def test_fields_descendants(self):
        response = self.get_response(fields='descendants')
        content = json.loads(response.content.decode('UTF-8'))

        for page in content['items']:
            descendants = page['meta']['descendants']
            self.assertEqual(set(descendants.keys()), {'count', 'listing_url'})
            self.assertIsInstance(descendants['count'], int)
            self.assertEqual(descendants['listing_url'], 'http://localhost/admin/api/main/pages/?descendant_of=%d' % page['id'])

    def test_fields_child_relation(self):
        response = self.get_response(type='demosite.BlogEntryPage', fields='title,related_links')
        content = json.loads(response.content.decode('UTF-8'))

        for page in content['items']:
            self.assertEqual(set(page.keys()), {'id', 'meta', 'title', 'admin_display_title', 'related_links'})
            self.assertIsInstance(page['related_links'], list)

    def test_fields_ordering(self):
        response = self.get_response(type='demosite.BlogEntryPage', fields='date,title,feed_image,related_links')

        # Will crash if the JSON is invalid
        content = json.loads(response.content.decode('UTF-8'))

        # Test field order
        content = json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode(response.content.decode('UTF-8'))
        field_order = [
            'id',
            'meta',
            'title',
            'admin_display_title',
            'date',
            'feed_image',
            'related_links',
        ]
        self.assertEqual(list(content['items'][0].keys()), field_order)

    def test_fields_tags(self):
        response = self.get_response(type='demosite.BlogEntryPage', fields='tags')
        content = json.loads(response.content.decode('UTF-8'))

        for page in content['items']:
            self.assertEqual(set(page.keys()), {'id', 'meta', 'tags', 'title', 'admin_display_title'})
            self.assertIsInstance(page['tags'], list)

    def test_fields_translations(self):
        # Add a translation of the homepage
        french = Locale.objects.create(language_code='fr')
        homepage = Page.objects.get(depth=2)
        french_homepage = homepage.copy_for_translation(french)

        response = self.get_response(fields='translations')
        content = json.loads(response.content.decode('UTF-8'))

        for page in content['items']:
            translations = page['meta']['translations']

            if page['id'] == homepage.id:
                self.assertEqual(len(translations), 1)
                self.assertEqual(translations[0]['id'], french_homepage.id)
                self.assertEqual(translations[0]['meta']['locale'], 'fr')

            elif page['id'] == french_homepage.id:
                self.assertEqual(len(translations), 1)
                self.assertEqual(translations[0]['id'], homepage.id)
                self.assertEqual(translations[0]['meta']['locale'], 'en')

            else:
                self.assertEqual(translations, [])

    # CHILD OF FILTER

    # Not applicable to the admin API
    test_child_of_page_thats_not_in_same_site_gives_error = None

    def test_child_of_root(self):
        # Only return the homepage as that's the only child of the "root" node
        # in the tree. This is different to the public API which pretends the
        # homepage of the current site is the root page.
        response = self.get_response(child_of='root')
        content = json.loads(response.content.decode('UTF-8'))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [2])

    def test_child_of_page_1(self):
        # Public API doesn't allow this, as it's the root page
        response = self.get_response(child_of=1)
        json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 200)

    # DESCENDANT OF FILTER

    # Not applicable to the admin API
    test_descendant_of_page_thats_not_in_same_site_gives_error = None

    def test_descendant_of_root(self):
        response = self.get_response(descendant_of='root')
        content = json.loads(response.content.decode('UTF-8'))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [2, 4, 8, 9, 5, 16, 18, 19, 6, 10, 15, 17, 21, 22, 23, 20, 13, 14, 12])

    def test_descendant_of_root_doesnt_give_error(self):
        # Public API doesn't allow this
        response = self.get_response(descendant_of=1)
        json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 200)

    # FOR EXPLORER FILTER

    def make_simple_page(self, parent, title):
        return parent.add_child(instance=SimplePage(title=title, content='Simple page'))

    def test_for_explorer_filter(self):
        movies = self.make_simple_page(Page.objects.get(pk=1), 'Movies')
        visible_movies = [
            self.make_simple_page(movies, 'The Way of the Dragon'),
            self.make_simple_page(movies, 'Enter the Dragon'),
            self.make_simple_page(movies, 'Dragons Forever'),
        ]
        hidden_movies = [
            self.make_simple_page(movies, 'The Hidden Fortress'),
            self.make_simple_page(movies, 'Crouching Tiger, Hidden Dragon'),
            self.make_simple_page(movies, 'Crouching Tiger, Hidden Dragon: Sword of Destiny'),
        ]

        response = self.get_response(child_of=movies.pk, for_explorer=1)
        content = json.loads(response.content.decode('UTF-8'))
        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [page.pk for page in visible_movies])

        response = self.get_response(child_of=movies.pk)
        content = json.loads(response.content.decode('UTF-8'))
        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [page.pk for page in visible_movies + hidden_movies])

    def test_for_explorer_no_child_of(self):
        response = self.get_response(for_explorer=1)
        self.assertEqual(response.status_code, 400)
        content = json.loads(response.content.decode('UTF-8'))
        self.assertEqual(content, {
            'message': 'filtering by for_explorer without child_of is not supported',
        })

    def test_for_explorer_construct_explorer_page_queryset_ordering(self):
        def set_custom_ordering(parent_page, pages, request):
            return pages.order_by('-title')

        with hooks.register_temporarily('construct_explorer_page_queryset', set_custom_ordering):
            response = self.get_response(for_explorer=True, child_of=2)

        content = json.loads(response.content.decode('UTF-8'))
        page_id_list = self.get_page_id_list(content)

        self.assertEqual(page_id_list, [6, 20, 4, 12, 5])

    # HAS CHILDREN FILTER

    def test_has_children_filter(self):
        response = self.get_response(has_children='true')
        content = json.loads(response.content.decode('UTF-8'))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [2, 4, 5, 6, 21, 20])

    def test_has_children_filter_off(self):
        response = self.get_response(has_children='false')
        content = json.loads(response.content.decode('UTF-8'))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [8, 9, 16, 18, 19, 10, 15, 17, 22, 23, 13, 14, 12])

    def test_has_children_filter_int(self):
        response = self.get_response(has_children=1)
        content = json.loads(response.content.decode('UTF-8'))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [2, 4, 5, 6, 21, 20])

    def test_has_children_filter_int_off(self):
        response = self.get_response(has_children=0)
        content = json.loads(response.content.decode('UTF-8'))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [8, 9, 16, 18, 19, 10, 15, 17, 22, 23, 13, 14, 12])

    def test_has_children_filter_invalid_integer(self):
        response = self.get_response(has_children=3)
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "has_children must be 'true' or 'false'"})

    def test_has_children_filter_invalid_value(self):
        response = self.get_response(has_children='yes')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {'message': "has_children must be 'true' or 'false'"})

    # TYPE FILTER

    def test_type_filter_items_are_all_blog_entries(self):
        response = self.get_response(type='demosite.BlogEntryPage')
        content = json.loads(response.content.decode('UTF-8'))

        for page in content['items']:
            self.assertEqual(page['meta']['type'], 'demosite.BlogEntryPage')

            # No specific fields available by default
            self.assertEqual(set(page.keys()), {'id', 'meta', 'title', 'admin_display_title'})

    def test_type_filter_multiple(self):
        response = self.get_response(type='demosite.BlogEntryPage,demosite.EventPage')
        content = json.loads(response.content.decode('UTF-8'))

        blog_page_seen = False
        event_page_seen = False

        for page in content['items']:
            self.assertIn(page['meta']['type'], ['demosite.BlogEntryPage', 'demosite.EventPage'])

            if page['meta']['type'] == 'demosite.BlogEntryPage':
                blog_page_seen = True
            elif page['meta']['type'] == 'demosite.EventPage':
                event_page_seen = True

            # Only generic fields available
            self.assertEqual(set(page.keys()), {'id', 'meta', 'title', 'admin_display_title'})

        self.assertTrue(blog_page_seen, "No blog pages were found in the items")
        self.assertTrue(event_page_seen, "No event pages were found in the items")


class TestAdminPageDetail(AdminAPITestCase, TestPageDetail):
    fixtures = ['demosite.json']

    def get_response(self, page_id, **params):
        return self.client.get(reverse('wagtailadmin_api:pages:detail', args=(page_id, )), params)

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
        self.assertEqual(content['meta']['detail_url'], 'http://localhost/admin/api/main/pages/16/')

        # Check the meta html_url
        self.assertIn('html_url', content['meta'])
        self.assertEqual(content['meta']['html_url'], 'http://localhost/blog-index/blog-post/')

        # Check the meta status

        self.assertIn('status', content['meta'])
        self.assertEqual(content['meta']['status'], {
            'status': 'live',
            'live': True,
            'has_unpublished_changes': False
        })

        # Check the meta children

        self.assertIn('children', content['meta'])
        self.assertEqual(content['meta']['children'], {
            'count': 0,
            'listing_url': 'http://localhost/admin/api/main/pages/?child_of=16'
        })

        # Check the parent field
        self.assertIn('parent', content['meta'])
        self.assertIsInstance(content['meta']['parent'], dict)
        self.assertEqual(set(content['meta']['parent'].keys()), {'id', 'meta', 'title'})
        self.assertEqual(content['meta']['parent']['id'], 5)
        self.assertIsInstance(content['meta']['parent']['meta'], dict)
        self.assertEqual(set(content['meta']['parent']['meta'].keys()), {'type', 'detail_url', 'html_url'})
        self.assertEqual(content['meta']['parent']['meta']['type'], 'demosite.BlogIndexPage')
        self.assertEqual(content['meta']['parent']['meta']['detail_url'], 'http://localhost/admin/api/main/pages/5/')
        self.assertEqual(content['meta']['parent']['meta']['html_url'], 'http://localhost/blog-index/')

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
        self.assertEqual(set(content['feed_image'].keys()), {'id', 'meta', 'title'})
        self.assertEqual(content['feed_image']['id'], 7)
        self.assertIsInstance(content['feed_image']['meta'], dict)
        self.assertEqual(set(content['feed_image']['meta'].keys()), {'type', 'detail_url', 'download_url'})
        self.assertEqual(content['feed_image']['meta']['type'], 'wagtailimages.Image')
        self.assertEqual(content['feed_image']['meta']['detail_url'], 'http://localhost/admin/api/main/images/7/')

        # Check that the child relations were serialised properly
        self.assertEqual(content['related_links'], [])
        for carousel_item in content['carousel_items']:
            self.assertEqual(set(carousel_item.keys()), {'id', 'meta', 'embed_url', 'link', 'caption', 'image'})
            self.assertEqual(set(carousel_item['meta'].keys()), {'type'})

        # Check the type info
        self.assertIsInstance(content['__types'], dict)
        self.assertEqual(set(content['__types'].keys()), {
            'wagtailcore.Page',
            'demosite.HomePage',
            'demosite.BlogIndexPage',
            'demosite.BlogEntryPageCarouselItem',
            'demosite.BlogEntryPage',
            'wagtailimages.Image'
        })
        self.assertEqual(set(content['__types']['demosite.BlogIndexPage'].keys()), {'verbose_name', 'verbose_name_plural'})
        self.assertEqual(content['__types']['demosite.BlogIndexPage']['verbose_name'], 'blog index page')
        self.assertEqual(content['__types']['demosite.BlogIndexPage']['verbose_name_plural'], 'blog index pages')

    # Overriden from public API tests
    def test_meta_parent_id_doesnt_show_root_page(self):
        # Root page is visible in the admin API
        response = self.get_response(2)
        content = json.loads(response.content.decode('UTF-8'))

        self.assertIsNotNone(content['meta']['parent'])

    def test_field_ordering(self):
        # Need to override this as the admin API has a __types field

        response = self.get_response(16)

        # Will crash if the JSON is invalid
        content = json.loads(response.content.decode('UTF-8'))

        # Test field order
        content = json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode(response.content.decode('UTF-8'))
        field_order = [
            'id',
            'meta',
            'title',
            'admin_display_title',
            'body',
            'tags',
            'date',
            'feed_image',
            'feed_image_thumbnail',
            'carousel_items',
            'related_links',
            '__types',
        ]
        self.assertEqual(list(content.keys()), field_order)

    def test_meta_status_draft(self):
        # Unpublish the page
        Page.objects.get(id=16).unpublish()

        response = self.get_response(16)
        content = json.loads(response.content.decode('UTF-8'))

        self.assertIn('status', content['meta'])
        self.assertEqual(content['meta']['status'], {
            'status': 'draft',
            'live': False,
            'has_unpublished_changes': True
        })

    def test_meta_status_live_draft(self):
        # Save revision without republish
        Page.objects.get(id=16).save_revision()

        response = self.get_response(16)
        content = json.loads(response.content.decode('UTF-8'))

        self.assertIn('status', content['meta'])
        self.assertEqual(content['meta']['status'], {
            'status': 'live + draft',
            'live': True,
            'has_unpublished_changes': True
        })

    def test_meta_status_scheduled(self):
        # Unpublish and save revision with go live date in the future
        Page.objects.get(id=16).unpublish()
        tomorrow = timezone.now() + datetime.timedelta(days=1)
        Page.objects.get(id=16).save_revision(approved_go_live_at=tomorrow)

        response = self.get_response(16)
        content = json.loads(response.content.decode('UTF-8'))

        self.assertIn('status', content['meta'])
        self.assertEqual(content['meta']['status'], {
            'status': 'scheduled',
            'live': False,
            'has_unpublished_changes': True
        })

    def test_meta_status_expired(self):
        # Unpublish and set expired flag
        Page.objects.get(id=16).unpublish()
        Page.objects.filter(id=16).update(expired=True)

        response = self.get_response(16)
        content = json.loads(response.content.decode('UTF-8'))

        self.assertIn('status', content['meta'])
        self.assertEqual(content['meta']['status'], {
            'status': 'expired',
            'live': False,
            'has_unpublished_changes': True
        })

    def test_meta_children_for_parent(self):
        # Homepage should have children
        response = self.get_response(2)
        content = json.loads(response.content.decode('UTF-8'))

        self.assertIn('children', content['meta'])
        self.assertEqual(content['meta']['children'], {
            'count': 5,
            'listing_url': 'http://localhost/admin/api/main/pages/?child_of=2'
        })

    def test_meta_descendants(self):
        # Homepage should have children
        response = self.get_response(2)
        content = json.loads(response.content.decode('UTF-8'))

        self.assertIn('descendants', content['meta'])
        self.assertEqual(content['meta']['descendants'], {
            'count': 18,
            'listing_url': 'http://localhost/admin/api/main/pages/?descendant_of=2'
        })

    def test_meta_ancestors(self):
        # Homepage should have children
        response = self.get_response(16)
        content = json.loads(response.content.decode('UTF-8'))

        self.assertIn('ancestors', content['meta'])
        self.assertIsInstance(content['meta']['ancestors'], list)
        self.assertEqual(len(content['meta']['ancestors']), 3)
        self.assertEqual(content['meta']['ancestors'][0].keys(), {'id', 'meta', 'title', 'admin_display_title'})
        self.assertEqual(content['meta']['ancestors'][0]['title'], 'Root')
        self.assertEqual(content['meta']['ancestors'][1]['title'], 'Home page')
        self.assertEqual(content['meta']['ancestors'][2]['title'], 'Blog index')

    # FIELDS

    def test_remove_all_meta_fields(self):
        response = self.get_response(16, fields='-type,-detail_url,-slug,-first_published_at,-html_url,-descendants,-latest_revision_created_at,-children,-ancestors,-show_in_menus,-seo_title,-parent,-status,-search_description')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertNotIn('meta', set(content.keys()))
        self.assertIn('id', set(content.keys()))

    def test_remove_all_fields(self):
        response = self.get_response(16, fields='_,id,type')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(set(content.keys()), {'id', 'meta', '__types'})
        self.assertEqual(set(content['meta'].keys()), {'type'})

    def test_all_nested_fields(self):
        response = self.get_response(16, fields='feed_image(*)')
        content = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(set(content['feed_image'].keys()), {'id', 'meta', 'title', 'width', 'height', 'thumbnail'})

    def test_fields_foreign_key(self):
        response = self.get_response(16)
        content = json.loads(response.content.decode('UTF-8'))

        feed_image = content['feed_image']

        self.assertIsInstance(feed_image, dict)
        self.assertEqual(set(feed_image.keys()), {'id', 'meta', 'title'})
        self.assertIsInstance(feed_image['id'], int)
        self.assertIsInstance(feed_image['meta'], dict)
        self.assertEqual(set(feed_image['meta'].keys()), {'type', 'detail_url', 'download_url'})
        self.assertEqual(feed_image['meta']['type'], 'wagtailimages.Image')
        self.assertEqual(feed_image['meta']['detail_url'], 'http://localhost/admin/api/main/images/%d/' % feed_image['id'])


class TestAdminPageDetailWithStreamField(AdminAPITestCase):
    fixtures = ['test.json']

    def setUp(self):
        super().setUp()

        self.homepage = Page.objects.get(url_path='/home/')

    def make_stream_page(self, body):
        stream_page = StreamPage(
            title='stream page',
            slug='stream-page',
            body=body
        )
        return self.homepage.add_child(instance=stream_page)

    def test_can_fetch_streamfield_content(self):
        stream_page = self.make_stream_page('[{"type": "text", "value": "foo"}]')

        response_url = reverse('wagtailadmin_api:pages:detail', args=(stream_page.id, ))
        response = self.client.get(response_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')

        content = json.loads(response.content.decode('utf-8'))

        self.assertIn('id', content)
        self.assertEqual(content['id'], stream_page.id)
        self.assertIn('body', content)
        self.assertEqual(len(content['body']), 1)
        self.assertEqual(content['body'][0]['type'], 'text')
        self.assertEqual(content['body'][0]['value'], 'foo')
        self.assertTrue(content['body'][0]['id'])

    def test_image_block(self):
        stream_page = self.make_stream_page('[{"type": "image", "value": 1}]')

        response_url = reverse('wagtailadmin_api:pages:detail', args=(stream_page.id, ))
        response = self.client.get(response_url)
        content = json.loads(response.content.decode('utf-8'))

        # ForeignKeys in a StreamField shouldn't be translated into dictionary representation
        self.assertEqual(content['body'][0]['type'], 'image')
        self.assertEqual(content['body'][0]['value'], 1)


class TestCustomAdminDisplayTitle(AdminAPITestCase):
    fixtures = ['test.json']

    def setUp(self):
        super().setUp()

        self.event_page = Page.objects.get(url_path='/home/events/saint-patrick/')

    def test_custom_admin_display_title_shown_on_detail_page(self):
        api_url = reverse('wagtailadmin_api:pages:detail', args=(self.event_page.id, ))
        response = self.client.get(api_url)
        content = json.loads(response.content.decode('utf-8'))

        self.assertEqual(content['title'], "Saint Patrick")
        self.assertEqual(content['admin_display_title'], "Saint Patrick (single event)")

    def test_custom_admin_display_title_shown_on_listing(self):
        api_url = reverse('wagtailadmin_api:pages:listing')
        response = self.client.get(api_url)
        content = json.loads(response.content.decode('utf-8'))

        matching_items = [item for item in content['items'] if item['id'] == self.event_page.id]
        self.assertEqual(1, len(matching_items))
        self.assertEqual(matching_items[0]['title'], "Saint Patrick")
        self.assertEqual(matching_items[0]['admin_display_title'], "Saint Patrick (single event)")


# Overwrite imported test cases do Django doesn't run them
TestPageDetail = None
TestPageListing = None
