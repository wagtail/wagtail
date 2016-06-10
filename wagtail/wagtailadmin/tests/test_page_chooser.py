from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse
from django.test import TestCase

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


class TestChooserBrowseWithChoosablePageRestrictions(TestCase, WagtailTestUtils):
    """
    See wagtail.wagtailadmin.tests.test_pages_views.TestExplorablePageVisibility for an explanation about
    how the DB is set up, as many of the same rules will apply to these tests.
    """

    fixtures = ['test_explorable_pages.json']

    def browse(self, **kwargs):
        return self.client.get(reverse('wagtailadmin_choose_page'), **kwargs)

    def browse_child(self, page_id, **kwargs):
        return self.client.get(reverse('wagtailadmin_choose_page_child', args=[page_id]), **kwargs)

    def test_default_browse_roots_tree_at_rootpage_for_superusers(self):
        self.assertTrue(self.client.login(username='superman', password='password'))
        response = self.browse()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['parent_page'].pk, 1)

    def test_default_browse_does_not_restrict_page_listing_for_superusers(self):
        self.assertTrue(self.client.login(username='superman', password='password'))
        response = self.browse()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['pages']), Page.get_first_root_node().get_children().count())
        # Confirm that the superuser can see all the homepages, which no other user in the fixture can do.
        self.assertSequenceEqual(
            ['Welcome to testserver!', 'Welcome to example.com!', 'Welcome to example.com Again!'],
            [page.title for page in response.context['pages']]
        )

    def test_default_browse_roots_tree_at_CCA_for_non_superusers(self):
        # Jane's CCA is the testserver homepage.
        self.assertTrue(self.client.login(username='jane', password='password'))
        response = self.browse()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['parent_page'].pk, 2)

        # Sam's CCA is the root page, since he has perms on both testserver and example.com.
        self.assertTrue(self.client.login(username='sam', password='password'))
        response = self.browse()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['parent_page'].pk, 1)

        # Josh's CCA is the example.com homepage.
        self.assertTrue(self.client.login(username='josh', password='password'))
        response = self.browse()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['parent_page'].pk, 4)

    def test_browse_restricts_page_listing_for_non_superusers(self):
        self.assertTrue(self.client.login(username='josh', password='password'))
        # Get the page listing rooted at the /home/content page on example.com. Josh should not see Page 2.
        response = self.browse_child(5)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['parent_page'].pk, 5)
        self.assertNotIn(Page.objects.get(pk=7), response.context['pages'])

    def test_non_superuser_browsing_unpermitted_site_page_gets_403(self):
        self.assertTrue(self.client.login(username='bob', password='password'))
        response = self.browse_child(7, HTTP_HOST="example.com")
        # Bob has permission to explore example.com's "Page 1", but not "Page 2", so the chooser should deny access.
        self.assertEqual(response.status_code, 403)

    def test_non_superuser_browsings_non_site_page_gets_404(self):
        self.assertTrue(self.client.login(username='jane', password='password'))
        response = self.browse_child(4)
        # Jane doesn't have permission to see the example.com homepage, and it's not associted with the current site,
        # so the Explorer should claim it doesn't exist.
        self.assertEqual(response.status_code, 404)

    def test_browsing_nonexistant_page_gets_404(self):
        self.assertTrue(self.client.login(username='superman', password='password'))
        # No Page exists with this ID.
        response = self.browse_child(9999999)
        self.assertEqual(response.status_code, 404)

    def test_browse_makes_required_ancesors_visible_but_not_choosable(self):
        self.assertTrue(self.client.login(username='sam', password='password'))
        # Get the page listing rooted at sam's CCA, which should be the root page.
        response = self.browse()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['parent_page'].pk, 1)
        # Josh should see the testserver homepage and example.com homepage.
        listed_pages = [page for page in response.context['pages']]
        self.assertSequenceEqual([2, 4], [page.pk for page in listed_pages])
        # Josh should not be able to choose the example.com homepage.
        self.assertFalse(listed_pages[1].can_choose)

        # Browse the tree at page 4, so we can confirm that the parent_page context var is also made unchoosable
        # when it's a required ancestor.
        response = self.browse_child(4)
        self.assertFalse(response.context['parent_page'].can_choose)


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


class TestChooserSearchWithChoosablePageRestrictions(TestCase, WagtailTestUtils):
    """
    See wagtail.wagtailadmin.tests.test_pages_views.TestExplorablePageVisibility for an explanation about
    how the DB is set up, as many of the same rules will apply to these tests.
    """

    fixtures = ['test_explorable_pages.json']

    def search(self, params=None):
        return self.client.get(reverse('wagtailadmin_choose_page_search'), params or {})

    def test_search_results_appear_for_permitted_user(self):
        # Jane should be able to see testserver's homepage.
        self.assertTrue(self.client.login(username='jane', password='password'))
        response = self.search({'q': 'testserver'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/chooser/_search_results.html')
        self.assertContains(response, "Welcome to testserver!")

    def test_search_results_exclude_unchoosable_pages(self):
        # Bob, however, should not see testserver's homepage, because he's not in a Group with permission to choose it.
        self.assertTrue(self.client.login(username='bob', password='password'))
        response = self.search({'q': 'testserver'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/chooser/_search_results.html')
        self.assertNotContains(response, "Welcome to testserver!")
        self.assertContains(response, 'There are 0 matches')

    def test_search_results_exclude_required_ancestors(self):
        self.assertTrue(self.client.login(username='josh', password='password'))
        response = self.search({'q': 'Other Content'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Other Content")

        # The example.com homepage is a required ancestor of Josh's permitted pages, so he can't choose it.
        # Thus, the Chooser search shouldn't include it.
        response = self.search({'q': 'Welcome to example.com!'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Welcome to example.com!")


class TestChooserExternalLink(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_choose_page_external_link'), params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailadmin_choose_page_external_link'), post_data)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/chooser/external_link.html')

    def test_get_with_param(self):
        self.assertEqual(self.get({'link_text': 'foo'}).status_code, 200)

    def test_create_link(self):
        response = self.post({'url': 'http://www.example.com/', 'link_text': 'example'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "'onload'")  # indicates success / post back to calling page
        self.assertContains(response, "'url': 'http://www.example.com/'")
        self.assertContains(response, "'title': 'example'")  # When link text is given, it is used

    def test_create_link_without_text(self):
        response = self.post({'url': 'http://www.example.com/'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "'onload'")  # indicates success / post back to calling page
        self.assertContains(response, "'url': 'http://www.example.com/'")
        self.assertContains(response, "'title': 'http://www.example.com/'")  # When no text is given, it uses the url

    def test_invalid_url(self):
        response = self.post({'url': 'ntp://www.example.com', 'link_text': 'example'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "'html'")  # indicates failure / show error message
        self.assertContains(response, "Enter a valid URL.")

    def test_allow_local_url(self):
        response = self.post({'url': '/admin/', 'link_text': 'admin'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "'onload'")  # indicates success / post back to calling page
        self.assertContains(response, "'url': '/admin/',")
        self.assertContains(response, "'title': 'admin'")


class TestChooserEmailLink(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_choose_page_email_link'), params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailadmin_choose_page_email_link'), post_data)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/chooser/email_link.html')

    def test_get_with_param(self):
        self.assertEqual(self.get({'link_text': 'foo'}).status_code, 200)

    def test_create_link(self):
        request = self.post({'email_address': 'example@example.com', 'link_text': 'contact'})
        self.assertContains(request, "'url': 'mailto:example@example.com',")
        self.assertContains(request, "'title': 'contact'")  # When link text is given, it is used

    def test_create_link_without_text(self):
        request = self.post({'email_address': 'example@example.com'})
        self.assertContains(request, "'url': 'mailto:example@example.com',")
        self.assertContains(request, "'title': 'example@example.com'")  # When no link text is given, it uses the email
