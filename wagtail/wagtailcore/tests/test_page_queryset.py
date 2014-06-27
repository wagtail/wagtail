from StringIO import StringIO

from django.test import TestCase, Client
from django.http import HttpRequest, Http404
from django.core import management
from django.contrib.auth.models import User

from wagtail.wagtailcore.models import Page, Site, UserPagePermissionsProxy
from wagtail.tests.models import EventPage, EventIndex, SimplePage


class TestPageQuerySet(TestCase):
    fixtures = ['test.json']

    def test_live(self):
        pages = Page.objects.live()

        # All pages must be live
        for page in pages:
            self.assertTrue(page.live)

        # Check that the homepage is in the results
        homepage = Page.objects.get(url_path='/home/')
        self.assertTrue(pages.filter(id=homepage.id).exists())

    def test_not_live(self):
        pages = Page.objects.not_live()

        # All pages must not be live
        for page in pages:
            self.assertFalse(page.live)

        # Check that "someone elses event" is in the results
        event = Page.objects.get(url_path='/home/events/someone-elses-event/')
        self.assertTrue(pages.filter(id=event.id).exists())

    def test_in_menu(self):
        pages = Page.objects.in_menu()

        # All pages must be be in the menus
        for page in pages:
            self.assertTrue(page.show_in_menus)

        # Check that the events index is in the results
        events_index = Page.objects.get(url_path='/home/events/')
        self.assertTrue(pages.filter(id=events_index.id).exists())

    def test_not_in_menu(self):
        pages = Page.objects.not_in_menu()

        # All pages must not be in menus
        for page in pages:
            self.assertFalse(page.show_in_menus)

        # Check that the root page is in the results
        self.assertTrue(pages.filter(id=1).exists())

    def test_page(self):
        homepage = Page.objects.get(url_path='/home/')
        pages = Page.objects.page(homepage)

        # Should only select the homepage
        self.assertEqual(pages.count(), 1)
        self.assertEqual(pages.first(), homepage)

    def test_not_page(self):
        homepage = Page.objects.get(url_path='/home/')
        pages = Page.objects.not_page(homepage)

        # Should select everything except for the homepage
        self.assertEqual(pages.count(), Page.objects.all().count() - 1)
        for page in pages:
            self.assertNotEqual(page, homepage)

    def test_descendant_of(self):
        events_index = Page.objects.get(url_path='/home/events/')
        pages = Page.objects.descendant_of(events_index)

        # Check that all pages descend from events index
        for page in pages:
            self.assertTrue(page.get_ancestors().filter(id=events_index.id).exists())

    def test_descendant_of_inclusive(self):
        events_index = Page.objects.get(url_path='/home/events/')
        pages = Page.objects.descendant_of(events_index, inclusive=True)

        # Check that all pages descend from events index, includes event index
        for page in pages:
            self.assertTrue(page == events_index or page.get_ancestors().filter(id=events_index.id).exists())

        # Check that event index was included
        self.assertTrue(pages.filter(id=events_index.id).exists())

    def test_not_descendant_of(self):
        homepage = Page.objects.get(url_path='/home/')
        events_index = Page.objects.get(url_path='/home/events/')
        pages = Page.objects.not_descendant_of(events_index)

        # Check that no pages descend from events_index
        for page in pages:
            self.assertFalse(page.get_ancestors().filter(id=events_index.id).exists())

        # As this is not inclusive, events index should be in the results
        self.assertTrue(pages.filter(id=events_index.id).exists())

    def test_not_descendant_of_inclusive(self):
        homepage = Page.objects.get(url_path='/home/')
        events_index = Page.objects.get(url_path='/home/events/')
        pages = Page.objects.not_descendant_of(events_index, inclusive=True)

        # Check that all pages descend from homepage but not events index
        for page in pages:
            self.assertFalse(page.get_ancestors().filter(id=events_index.id).exists())

        # As this is inclusive, events index should not be in the results
        self.assertFalse(pages.filter(id=events_index.id).exists())

    def test_child_of(self):
        homepage = Page.objects.get(url_path='/home/')
        pages = Page.objects.child_of(homepage)

        # Check that all pages are children of homepage
        for page in pages:
            self.assertEqual(page.get_parent(), homepage)

    def test_not_child_of(self):
        events_index = Page.objects.get(url_path='/home/events/')
        pages = Page.objects.not_child_of(events_index)

        # Check that all pages are not children of events_index
        for page in pages:
            self.assertNotEqual(page.get_parent(), events_index)

    def test_ancestor_of(self):
        root_page = Page.objects.get(id=1)
        homepage = Page.objects.get(url_path='/home/')
        events_index = Page.objects.get(url_path='/home/events/')
        pages = Page.objects.ancestor_of(events_index)

        self.assertEqual(pages.count(), 2)
        self.assertEqual(pages[0], root_page)
        self.assertEqual(pages[1], homepage)

    def test_ancestor_of_inclusive(self):
        root_page = Page.objects.get(id=1)
        homepage = Page.objects.get(url_path='/home/')
        events_index = Page.objects.get(url_path='/home/events/')
        pages = Page.objects.ancestor_of(events_index, inclusive=True)

        self.assertEqual(pages.count(), 3)
        self.assertEqual(pages[0], root_page)
        self.assertEqual(pages[1], homepage)
        self.assertEqual(pages[2], events_index)

    def test_not_ancestor_of(self):
        root_page = Page.objects.get(id=1)
        homepage = Page.objects.get(url_path='/home/')
        events_index = Page.objects.get(url_path='/home/events/')
        pages = Page.objects.not_ancestor_of(events_index)

        # Test that none of the ancestors are in pages
        for page in pages:
            self.assertNotEqual(page, root_page)
            self.assertNotEqual(page, homepage)

        # Test that events index is in pages
        self.assertTrue(pages.filter(id=events_index.id).exists())

    def test_not_ancestor_of_inclusive(self):
        root_page = Page.objects.get(id=1)
        homepage = Page.objects.get(url_path='/home/')
        events_index = Page.objects.get(url_path='/home/events/')
        pages = Page.objects.not_ancestor_of(events_index, inclusive=True)

        # Test that none of the ancestors or the events_index are in pages
        for page in pages:
            self.assertNotEqual(page, root_page)
            self.assertNotEqual(page, homepage)
            self.assertNotEqual(page, events_index)

    def test_parent_of(self):
        homepage = Page.objects.get(url_path='/home/')
        events_index = Page.objects.get(url_path='/home/events/')
        pages = Page.objects.parent_of(events_index)

        # Pages must only contain homepage
        self.assertEqual(pages.count(), 1)
        self.assertEqual(pages[0], homepage)

    def test_not_parent_of(self):
        homepage = Page.objects.get(url_path='/home/')
        events_index = Page.objects.get(url_path='/home/events/')
        pages = Page.objects.not_parent_of(events_index)

        # Pages must not contain homepage
        for page in pages:
            self.assertNotEqual(page, homepage)

        # Test that events index is in pages
        self.assertTrue(pages.filter(id=events_index.id).exists())

    def test_sibling_of(self):
        events_index = Page.objects.get(url_path='/home/events/')
        event = Page.objects.get(url_path='/home/events/christmas/')
        pages = Page.objects.sibling_of(event)

        # Check that all pages are children of events_index
        for page in pages:
            self.assertEqual(page.get_parent(), events_index)

        # Check that the event is not included
        self.assertFalse(pages.filter(id=event.id).exists())

    def test_sibling_of_inclusive(self):
        events_index = Page.objects.get(url_path='/home/events/')
        event = Page.objects.get(url_path='/home/events/christmas/')
        pages = Page.objects.sibling_of(event, inclusive=True)

        # Check that all pages are children of events_index
        for page in pages:
            self.assertEqual(page.get_parent(), events_index)

        # Check that the event is included
        self.assertTrue(pages.filter(id=event.id).exists())

    def test_not_sibling_of(self):
        events_index = Page.objects.get(url_path='/home/events/')
        event = Page.objects.get(url_path='/home/events/christmas/')
        pages = Page.objects.not_sibling_of(event)

        # Check that all pages are not children of events_index
        for page in pages:
            if page != event:
                self.assertNotEqual(page.get_parent(), events_index)

        # Check that the event is included
        self.assertTrue(pages.filter(id=event.id).exists())

        # Test that events index is in pages
        self.assertTrue(pages.filter(id=events_index.id).exists())

    def test_not_sibling_of_inclusive(self):
        events_index = Page.objects.get(url_path='/home/events/')
        event = Page.objects.get(url_path='/home/events/christmas/')
        pages = Page.objects.not_sibling_of(event, inclusive=True)

        # Check that all pages are not children of events_index
        for page in pages:
            self.assertNotEqual(page.get_parent(), events_index)

        # Check that the event is not included
        self.assertFalse(pages.filter(id=event.id).exists())

        # Test that events index is in pages
        self.assertTrue(pages.filter(id=events_index.id).exists())

    def test_type(self):
        pages = Page.objects.type(EventPage)

        # Check that all objects are EventPages
        for page in pages:
            self.assertIsInstance(page.specific, EventPage)

        # Check that "someone elses event" is in the results
        event = Page.objects.get(url_path='/home/events/someone-elses-event/')
        self.assertTrue(pages.filter(id=event.id).exists())

    def test_not_type(self):
        pages = Page.objects.not_type(EventPage)

        # Check that no objects are EventPages
        for page in pages:
            self.assertNotIsInstance(page.specific, EventPage)

        # Check that the homepage is in the results
        homepage = Page.objects.get(url_path='/home/')
        self.assertTrue(pages.filter(id=homepage.id).exists())
