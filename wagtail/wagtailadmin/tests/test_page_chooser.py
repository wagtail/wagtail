from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.http import urlencode

from wagtail.tests.testapp.models import EventIndex, EventPage, SimplePage
from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailcore.models import Page


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
        self.assertContains(response, "There is one match")
        self.assertContains(response, "foobarbaz")

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
        self.assertContains(response, "There is one match")
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
        self.assertContains(response, "'onload'")  # indicates success / post back to calling page
        self.assertContains(response, '"url": "http://www.example.com/"')
        self.assertContains(response, '"title": "example"')  # When link text is given, it is used
        self.assertContains(response, '"prefer_this_title_as_link_text": true')

    def test_create_link_without_text(self):
        response = self.post({'url': 'http://www.example.com/'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "'onload'")  # indicates success / post back to calling page
        self.assertContains(response, '"url": "http://www.example.com/"')
        self.assertContains(response, '"title": "http://www.example.com/"')  # When no text is given, it uses the url
        self.assertContains(response, '"prefer_this_title_as_link_text": false')

    def test_notice_changes_to_link_text(self):
        response = self.post(
            {'url': 'http://www.example.com/', 'link_text': 'example'},  # POST data
            {'link_url': 'http://old.example.com/', 'link_text': 'example'}  # GET params - initial data
        )
        self.assertContains(response, '"url": "http://www.example.com/"')
        self.assertContains(response, '"title": "example"')
        # no change to link text, so prefer the existing link/selection content where available
        self.assertContains(response, '"prefer_this_title_as_link_text": false')

        response = self.post(
            {'url': 'http://www.example.com/', 'link_text': 'new example'},  # POST data
            {'link_url': 'http://old.example.com/', 'link_text': 'example'}  # GET params - initial data
        )
        self.assertContains(response, '"url": "http://www.example.com/"')
        self.assertContains(response, '"title": "new example"')
        # link text has changed, so tell the caller to use it
        self.assertContains(response, '"prefer_this_title_as_link_text": true')

    def test_invalid_url(self):
        response = self.post({'url': 'ntp://www.example.com', 'link_text': 'example'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "'html'")  # indicates failure / show error message
        self.assertContains(response, "Enter a valid URL.")

    def test_allow_local_url(self):
        response = self.post({'url': '/admin/', 'link_text': 'admin'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "'onload'")  # indicates success / post back to calling page
        self.assertContains(response, '"url": "/admin/"')
        self.assertContains(response, '"title": "admin"')


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
        self.assertContains(response, '"url": "mailto:example@example.com"')
        self.assertContains(response, '"title": "contact"')  # When link text is given, it is used
        self.assertContains(response, '"prefer_this_title_as_link_text": true')

    def test_create_link_without_text(self):
        response = self.post({'email_address': 'example@example.com'})
        self.assertContains(response, '"url": "mailto:example@example.com"')
        self.assertContains(response, '"title": "example@example.com"')  # When no link text is given, it uses the email
        self.assertContains(response, '"prefer_this_title_as_link_text": false')

    def test_notice_changes_to_link_text(self):
        response = self.post(
            {'email_address': 'example2@example.com', 'link_text': 'example'},  # POST data
            {'link_url': 'example@example.com', 'link_text': 'example'}  # GET params - initial data
        )
        self.assertContains(response, '"url": "mailto:example2@example.com"')
        self.assertContains(response, '"title": "example"')
        # no change to link text, so prefer the existing link/selection content where available
        self.assertContains(response, '"prefer_this_title_as_link_text": false')

        response = self.post(
            {'email_address': 'example2@example.com', 'link_text': 'new example'},  # POST data
            {'link_url': 'example@example.com', 'link_text': 'example'}  # GET params - initial data
        )
        self.assertContains(response, '"url": "mailto:example2@example.com"')
        self.assertContains(response, '"title": "new example"')
        # link text has changed, so tell the caller to use it
        self.assertContains(response, '"prefer_this_title_as_link_text": true')
