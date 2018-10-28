import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.http import urlencode

from wagtail.admin.views.chooser import can_choose_page
from wagtail.core.models import Page, UserPagePermissionsProxy
from wagtail.tests.testapp.models import EventIndex, EventPage, SimplePage, SingleEventPage
from wagtail.tests.utils import WagtailTestUtils


class TestChooserBrowse(TestCase, WagtailTestUtils):
    def setUp(self):
        self.root_page = Page.objects.get(id=2)

        # Add child page
        self.child_page = SimplePage(title="foobarbaz", content="hello")
        self.root_page.add_child(instance=self.child_page)

        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_choose_page'), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/chooser/browse.html')

    def test_construct_queryset_hook(self):
        page = SimplePage(title="Test shown", content="hello")
        Page.get_first_root_node().add_child(instance=page)

        page_not_shown = SimplePage(title="Test not shown", content="hello")
        Page.get_first_root_node().add_child(instance=page_not_shown)

        def filter_pages(pages, request):
            return pages.filter(id=page.id)

        with self.register_hook('construct_page_chooser_queryset', filter_pages):
            response = self.get()
        self.assertEqual(len(response.context['pages']), 1)
        self.assertEqual(response.context['pages'][0].specific, page)


class TestCanChooseRootFlag(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_choose_page'), params)

    def test_cannot_choose_root_by_default(self):
        response = self.get()
        self.assertNotContains(response, '/admin/pages/1/edit/')

    def test_can_choose_root(self):
        response = self.get({'can_choose_root': 'true'})
        self.assertContains(response, '/admin/pages/1/edit/')


class TestChooserBrowseChild(TestCase, WagtailTestUtils):
    def setUp(self):
        self.root_page = Page.objects.get(id=2)

        # Add child page
        self.child_page = SimplePage(title="foobarbaz", content="hello")
        self.root_page.add_child(instance=self.child_page)

        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_choose_page_child',
                                       args=(self.root_page.id,)), params)

    def get_invalid(self, params={}):
        return self.client.get(reverse('wagtailadmin_choose_page_child',
                                       args=(9999999,)), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/chooser/browse.html')

    def test_get_invalid(self):
        self.assertEqual(self.get_invalid().status_code, 404)

    def test_with_page_type(self):
        # Add a page that is not a SimplePage
        event_page = EventPage(
            title="event",
            location='the moon', audience='public',
            cost='free', date_from='2001-01-01',
        )
        self.root_page.add_child(instance=event_page)

        # Add a page with a child page
        event_index_page = EventIndex(
            title="events",
        )
        self.root_page.add_child(instance=event_index_page)
        event_index_page.add_child(instance=EventPage(
            title="other event",
            location='the moon', audience='public',
            cost='free', date_from='2001-01-01',
        ))

        # Send request
        response = self.get({'page_type': 'tests.simplepage'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/chooser/browse.html')
        self.assertEqual(response.context['page_type_string'], 'tests.simplepage')

        pages = {
            page.id: page
            for page in response.context['pages'].object_list
        }

        # Child page is a simple page directly underneath root
        # so should appear in the list
        self.assertIn(self.child_page.id, pages)
        self.assertTrue(pages[self.child_page.id].can_choose)
        self.assertFalse(pages[self.child_page.id].can_descend)

        # Event page is not a simple page and is not descendable either
        # so should not appear in the list
        self.assertNotIn(event_page.id, pages)

        # Event index page is not a simple page but has a child and is therefore descendable
        # so should appear in the list
        self.assertIn(event_index_page.id, pages)
        self.assertFalse(pages[event_index_page.id].can_choose)
        self.assertTrue(pages[event_index_page.id].can_descend)

    def test_with_url_extended_page_type(self):
        # Add a page that overrides the url path
        single_event_page = SingleEventPage(
            title="foo",
            location='the moon', audience='public',
            cost='free', date_from='2001-01-01',
        )
        self.root_page.add_child(instance=single_event_page)

        # Send request
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/chooser/browse.html')

        page_urls = [
            page.url
            for page in response.context['pages']
        ]

        self.assertIn('/foo/pointless-suffix/', page_urls)

    def test_with_blank_page_type(self):
        # a blank page_type parameter should be equivalent to an absent parameter
        # (or an explicit page_type of wagtailcore.page)
        response = self.get({'page_type': ''})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/chooser/browse.html')

    def test_with_multiple_page_types(self):
        # Add a page that is not a SimplePage
        event_page = EventPage(
            title="event",
            location='the moon', audience='public',
            cost='free', date_from='2001-01-01',
        )
        self.root_page.add_child(instance=event_page)

        # Send request
        response = self.get({'page_type': 'tests.simplepage,tests.eventpage'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/chooser/browse.html')
        self.assertEqual(response.context['page_type_string'], 'tests.simplepage,tests.eventpage')

        pages = {
            page.id: page
            for page in response.context['pages'].object_list
        }

        # Simple page in results, as before
        self.assertIn(self.child_page.id, pages)
        self.assertTrue(pages[self.child_page.id].can_choose)

        # Event page should now also be choosable
        self.assertIn(event_page.id, pages)
        self.assertTrue(pages[self.child_page.id].can_choose)

    def test_with_unknown_page_type(self):
        response = self.get({'page_type': 'foo.bar'})
        self.assertEqual(response.status_code, 404)

    def test_with_bad_page_type(self):
        response = self.get({'page_type': 'wagtailcore.site'})
        self.assertEqual(response.status_code, 404)

    def test_with_invalid_page_type(self):
        response = self.get({'page_type': 'foo'})
        self.assertEqual(response.status_code, 404)

    def setup_pagination_test_data(self):
        # Create lots of pages
        for i in range(100):
            new_page = SimplePage(
                title="foobarbaz",
                slug="foobarbaz-%d" % i,
                content="hello",
            )
            self.root_page.add_child(instance=new_page)

    def test_pagination_basic(self):
        self.setup_pagination_test_data()

        response = self.get()
        self.assertEqual(response.context['pages'].paginator.num_pages, 5)
        self.assertEqual(response.context['pages'].number, 1)

    def test_pagination_another_page(self):
        self.setup_pagination_test_data()

        response = self.get({'p': 2})
        self.assertEqual(response.context['pages'].number, 2)

    def test_pagination_invalid_page(self):
        self.setup_pagination_test_data()

        response = self.get({'p': 'foo'})
        self.assertEqual(response.context['pages'].number, 1)

    def test_pagination_out_of_range_page(self):
        self.setup_pagination_test_data()

        response = self.get({'p': 100})
        self.assertEqual(response.context['pages'].number, 5)


class TestChooserSearch(TestCase, WagtailTestUtils):
    def setUp(self):
        self.root_page = Page.objects.get(id=2)

        # Add child page
        self.child_page = SimplePage(title="foobarbaz", content="hello")
        self.root_page.add_child(instance=self.child_page)

        self.login()

    def get(self, params=None):
        return self.client.get(reverse('wagtailadmin_choose_page_search'), params or {})

    def test_simple(self):
        response = self.get({'q': "foobarbaz"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/chooser/_search_results.html')
        self.assertContains(response, "There is 1 match")
        self.assertContains(response, "foobarbaz")

    def test_result_uses_custom_admin_display_title(self):
        single_event_page = SingleEventPage(
            title="Lunar event",
            location='the moon', audience='public',
            cost='free', date_from='2001-01-01',
        )
        self.root_page.add_child(instance=single_event_page)

        response = self.get({'q': "lunar"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/chooser/_search_results.html')
        self.assertContains(response, "Lunar event (single event)")

    def test_search_no_results(self):
        response = self.get({'q': "quux"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "There are 0 matches")

    def test_with_page_type(self):
        # Add a page that is not a SimplePage
        event_page = EventPage(
            title="foo",
            location='the moon', audience='public',
            cost='free', date_from='2001-01-01',
        )
        self.root_page.add_child(instance=event_page)

        # Send request
        response = self.get({'q': "foo", 'page_type': 'tests.simplepage'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/chooser/_search_results.html')
        self.assertEqual(response.context['page_type_string'], 'tests.simplepage')

        pages = {
            page.id: page
            for page in response.context['pages']
        }

        self.assertIn(self.child_page.id, pages)

        # Not a simple page
        self.assertNotIn(event_page.id, pages)

    def test_with_blank_page_type(self):
        # a blank page_type parameter should be equivalent to an absent parameter
        # (or an explicit page_type of wagtailcore.page)
        response = self.get({'q': "foobarbaz", 'page_type': ''})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/chooser/_search_results.html')
        self.assertContains(response, "There is 1 match")
        self.assertContains(response, "foobarbaz")

    def test_with_multiple_page_types(self):
        # Add a page that is not a SimplePage
        event_page = EventPage(
            title="foo",
            location='the moon', audience='public',
            cost='free', date_from='2001-01-01',
        )
        self.root_page.add_child(instance=event_page)

        # Send request
        response = self.get({'q': "foo", 'page_type': 'tests.simplepage,tests.eventpage'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/chooser/_search_results.html')
        self.assertEqual(response.context['page_type_string'], 'tests.simplepage,tests.eventpage')

        pages = {
            page.id: page
            for page in response.context['pages']
        }

        # Simple page in results, as before
        self.assertIn(self.child_page.id, pages)

        # Event page should now also be choosable
        self.assertIn(event_page.id, pages)

    def test_with_unknown_page_type(self):
        response = self.get({'page_type': 'foo.bar'})
        self.assertEqual(response.status_code, 404)

    def test_with_bad_page_type(self):
        response = self.get({'page_type': 'wagtailcore.site'})
        self.assertEqual(response.status_code, 404)

    def test_with_invalid_page_type(self):
        response = self.get({'page_type': 'foo'})
        self.assertEqual(response.status_code, 404)

    def test_construct_queryset_hook(self):
        page = SimplePage(title="Test shown", content="hello")
        self.root_page.add_child(instance=page)

        page_not_shown = SimplePage(title="Test not shown", content="hello")
        self.root_page.add_child(instance=page_not_shown)

        def filter_pages(pages, request):
            return pages.filter(id=page.id)

        with self.register_hook('construct_page_chooser_queryset', filter_pages):
            response = self.get({'q': 'Test'})
        self.assertEqual(len(response.context['pages']), 1)
        self.assertEqual(response.context['pages'][0].specific, page)


class TestAutomaticRootPageDetection(TestCase, WagtailTestUtils):
    def setUp(self):
        self.tree_root = Page.objects.get(id=1)
        self.home_page = Page.objects.get(id=2)

        self.about_page = self.home_page.add_child(instance=SimplePage(
            title='About', content='About Foo'))
        self.contact_page = self.about_page.add_child(instance=SimplePage(
            title='Contact', content='Content Foo'))
        self.people_page = self.about_page.add_child(instance=SimplePage(
            title='People', content='The people of Foo'))

        self.event_index = self.make_event_section('Events')

        self.login()

    def make_event_section(self, name):
        event_index = self.home_page.add_child(instance=EventIndex(
            title=name))
        event_index.add_child(instance=EventPage(
            title='First Event',
            location='Bar', audience='public',
            cost='free', date_from='2001-01-01'))
        event_index.add_child(instance=EventPage(
            title='Second Event',
            location='Baz', audience='public',
            cost='free', date_from='2001-01-01'))
        return event_index

    def get_best_root(self, params={}):
        response = self.client.get(reverse('wagtailadmin_choose_page'), params)
        return response.context['parent_page'].specific

    def test_no_type_filter(self):
        self.assertEqual(self.get_best_root(), self.tree_root)

    def test_type_page(self):
        self.assertEqual(
            self.get_best_root({'page_type': 'wagtailcore.Page'}),
            self.tree_root)

    def test_type_eventpage(self):
        """
        The chooser should start at the EventIndex that holds all the
        EventPages.
        """
        self.assertEqual(
            self.get_best_root({'page_type': 'tests.EventPage'}),
            self.event_index)

    def test_type_eventpage_two_indexes(self):
        """
        The chooser should start at the home page, as there are two
        EventIndexes with EventPages.
        """
        self.make_event_section('Other events')
        self.assertEqual(
            self.get_best_root({'page_type': 'tests.EventPage'}),
            self.home_page)

    def test_type_simple_page(self):
        """
        The chooser should start at the home page, as all SimplePages are
        directly under it
        """
        self.assertEqual(
            self.get_best_root({'page_type': 'tests.BusinessIndex'}),
            self.tree_root)

    def test_type_missing(self):
        """
        The chooser should start at the root, as there are no BusinessIndexes
        """
        self.assertEqual(
            self.get_best_root({'page_type': 'tests.BusinessIndex'}),
            self.tree_root)


class TestChooserExternalLink(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_choose_page_external_link'), params)

    def post(self, post_data={}, url_params={}):
        url = reverse('wagtailadmin_choose_page_external_link')
        if url_params:
            url += '?' + urlencode(url_params)
        return self.client.post(url, post_data)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/chooser/external_link.html')

    def test_prepopulated_form(self):
        response = self.get({'link_text': 'Torchbox', 'link_url': 'https://torchbox.com/'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Torchbox')
        self.assertContains(response, 'https://torchbox.com/')

    def test_create_link(self):
        response = self.post({'url': 'http://www.example.com/', 'link_text': 'example'})
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['step'], 'external_link_chosen')
        self.assertEqual(response_json['result']['url'], "http://www.example.com/")
        self.assertEqual(response_json['result']['title'], "example")  # When link text is given, it is used
        self.assertEqual(response_json['result']['prefer_this_title_as_link_text'], True)

    def test_create_link_without_text(self):
        response = self.post({'url': 'http://www.example.com/'})
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['step'], 'external_link_chosen')
        self.assertEqual(response_json['result']['url'], "http://www.example.com/")
        self.assertEqual(response_json['result']['title'], "http://www.example.com/")  # When no text is given, it uses the url
        self.assertEqual(response_json['result']['prefer_this_title_as_link_text'], False)

    def test_notice_changes_to_link_text(self):
        response = self.post(
            {'url': 'http://www.example.com/', 'link_text': 'example'},  # POST data
            {'link_url': 'http://old.example.com/', 'link_text': 'example'}  # GET params - initial data
        )
        result = json.loads(response.content.decode())['result']
        self.assertEqual(result['url'], "http://www.example.com/")
        self.assertEqual(result['title'], "example")
        # no change to link text, so prefer the existing link/selection content where available
        self.assertEqual(result['prefer_this_title_as_link_text'], False)

        response = self.post(
            {'url': 'http://www.example.com/', 'link_text': 'new example'},  # POST data
            {'link_url': 'http://old.example.com/', 'link_text': 'example'}  # GET params - initial data
        )
        result = json.loads(response.content.decode())['result']
        self.assertEqual(result['url'], "http://www.example.com/")
        self.assertEqual(result['title'], "new example")
        # link text has changed, so tell the caller to use it
        self.assertEqual(result['prefer_this_title_as_link_text'], True)

    def test_invalid_url(self):
        response = self.post({'url': 'ntp://www.example.com', 'link_text': 'example'})
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['step'], 'external_link')  # indicates failure / show error message
        self.assertContains(response, "Enter a valid URL.")

    def test_allow_local_url(self):
        response = self.post({'url': '/admin/', 'link_text': 'admin'})
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['step'], 'external_link_chosen')  # indicates success / post back to calling page
        self.assertEqual(response_json['result']['url'], "/admin/")
        self.assertEqual(response_json['result']['title'], "admin")


class TestChooserEmailLink(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_choose_page_email_link'), params)

    def post(self, post_data={}, url_params={}):
        url = reverse('wagtailadmin_choose_page_email_link')
        if url_params:
            url += '?' + urlencode(url_params)
        return self.client.post(url, post_data)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/chooser/email_link.html')

    def test_prepopulated_form(self):
        response = self.get({'link_text': 'Example', 'link_url': 'example@example.com'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Example')
        self.assertContains(response, 'example@example.com')

    def test_create_link(self):
        response = self.post({'email_address': 'example@example.com', 'link_text': 'contact'})
        result = json.loads(response.content.decode())['result']
        self.assertEqual(result['url'], "mailto:example@example.com")
        self.assertEqual(result['title'], "contact")  # When link text is given, it is used
        self.assertEqual(result['prefer_this_title_as_link_text'], True)

    def test_create_link_without_text(self):
        response = self.post({'email_address': 'example@example.com'})
        result = json.loads(response.content.decode())['result']
        self.assertEqual(result['url'], "mailto:example@example.com")
        self.assertEqual(result['title'], "example@example.com")  # When no link text is given, it uses the email
        self.assertEqual(result['prefer_this_title_as_link_text'], False)

    def test_notice_changes_to_link_text(self):
        response = self.post(
            {'email_address': 'example2@example.com', 'link_text': 'example'},  # POST data
            {'link_url': 'example@example.com', 'link_text': 'example'}  # GET params - initial data
        )
        result = json.loads(response.content.decode())['result']
        self.assertEqual(result['url'], "mailto:example2@example.com")
        self.assertEqual(result['title'], "example")
        # no change to link text, so prefer the existing link/selection content where available
        self.assertEqual(result['prefer_this_title_as_link_text'], False)

        response = self.post(
            {'email_address': 'example2@example.com', 'link_text': 'new example'},  # POST data
            {'link_url': 'example@example.com', 'link_text': 'example'}  # GET params - initial data
        )
        result = json.loads(response.content.decode())['result']
        self.assertEqual(result['url'], "mailto:example2@example.com")
        self.assertEqual(result['title'], "new example")
        # link text has changed, so tell the caller to use it
        self.assertEqual(result['prefer_this_title_as_link_text'], True)


class TestCanChoosePage(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.user = self.login()
        self.permission_proxy = UserPagePermissionsProxy(self.user)
        self.desired_classes = (Page, )

    def test_can_choose_page(self):
        homepage = Page.objects.get(url_path='/home/')
        result = can_choose_page(homepage, self.permission_proxy, self.desired_classes)
        self.assertTrue(result)

    def test_with_user_no_permission(self):
        homepage = Page.objects.get(url_path='/home/')
        # event editor does not have permissions on homepage
        event_editor = get_user_model().objects.get(username='eventeditor')
        permission_proxy = UserPagePermissionsProxy(event_editor)
        result = can_choose_page(homepage, permission_proxy, self.desired_classes, user_perm='copy_to')
        self.assertFalse(result)

    def test_with_can_choose_root(self):
        root = Page.objects.get(url_path='/')
        result = can_choose_page(root, self.permission_proxy, self.desired_classes, can_choose_root=True)
        self.assertTrue(result)

    def test_with_can_not_choose_root(self):
        root = Page.objects.get(url_path='/')
        result = can_choose_page(root, self.permission_proxy, self.desired_classes, can_choose_root=False)
        self.assertFalse(result)
