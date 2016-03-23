from django.test import TestCase

from wagtail.wagtailcore.models import Page, PageViewRestriction
from wagtail.wagtailcore.signals import page_unpublished
from wagtail.tests.testapp.models import EventPage, SingleEventPage


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
        events_index = Page.objects.get(url_path='/home/events/')
        pages = Page.objects.not_descendant_of(events_index)

        # Check that no pages descend from events_index
        for page in pages:
            self.assertFalse(page.get_ancestors().filter(id=events_index.id).exists())

        # As this is not inclusive, events index should be in the results
        self.assertTrue(pages.filter(id=events_index.id).exists())

    def test_not_descendant_of_inclusive(self):
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

    def test_sibling_of_default(self):
        """
        sibling_of should default to an inclusive definition of sibling
        if 'inclusive' flag not passed
        """
        events_index = Page.objects.get(url_path='/home/events/')
        event = Page.objects.get(url_path='/home/events/christmas/')
        pages = Page.objects.sibling_of(event)

        # Check that all pages are children of events_index
        for page in pages:
            self.assertEqual(page.get_parent(), events_index)

        # Check that the event is included
        self.assertTrue(pages.filter(id=event.id).exists())

    def test_sibling_of_exclusive(self):
        events_index = Page.objects.get(url_path='/home/events/')
        event = Page.objects.get(url_path='/home/events/christmas/')
        pages = Page.objects.sibling_of(event, inclusive=False)

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

    def test_not_sibling_of_default(self):
        """
        not_sibling_of should default to an inclusive definition of sibling -
        i.e. eliminate self from the results as well -
        if 'inclusive' flag not passed
        """
        events_index = Page.objects.get(url_path='/home/events/')
        event = Page.objects.get(url_path='/home/events/christmas/')
        pages = Page.objects.not_sibling_of(event)

        # Check that all pages are not children of events_index
        for page in pages:
            self.assertNotEqual(page.get_parent(), events_index)

        # Check that the event is not included
        self.assertFalse(pages.filter(id=event.id).exists())

        # Test that events index is in pages
        self.assertTrue(pages.filter(id=events_index.id).exists())

    def test_not_sibling_of_exclusive(self):
        events_index = Page.objects.get(url_path='/home/events/')
        event = Page.objects.get(url_path='/home/events/christmas/')
        pages = Page.objects.not_sibling_of(event, inclusive=False)

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

        # Check that "Saint Patrick" (an instance of SingleEventPage, a subclass of EventPage)
        # is in the results
        event = Page.objects.get(url_path='/home/events/saint-patrick/')
        self.assertTrue(pages.filter(id=event.id).exists())

    def test_type_includes_subclasses(self):
        from wagtail.wagtailforms.models import AbstractEmailForm
        pages = Page.objects.type(AbstractEmailForm)

        # Check that all objects are instances of AbstractEmailForm
        for page in pages:
            self.assertIsInstance(page.specific, AbstractEmailForm)

        # Check that the contact form page is in the results
        contact_us = Page.objects.get(url_path='/home/contact-us/')
        self.assertTrue(pages.filter(id=contact_us.id).exists())

    def test_not_type(self):
        pages = Page.objects.not_type(EventPage)

        # Check that no objects are EventPages
        for page in pages:
            self.assertNotIsInstance(page.specific, EventPage)

        # Check that the homepage is in the results
        homepage = Page.objects.get(url_path='/home/')
        self.assertTrue(pages.filter(id=homepage.id).exists())

    def test_exact_type(self):
        pages = Page.objects.exact_type(EventPage)

        # Check that all objects are EventPages (and not a subclass)
        for page in pages:
            self.assertEqual(type(page.specific), EventPage)

        # Check that "someone elses event" is in the results
        event = Page.objects.get(url_path='/home/events/someone-elses-event/')
        self.assertTrue(pages.filter(id=event.id).exists())

        # Check that "Saint Patrick" (an instance of SingleEventPage, a subclass of EventPage)
        # is NOT in the results
        event = Page.objects.get(url_path='/home/events/saint-patrick/')
        self.assertFalse(pages.filter(id=event.id).exists())

    def test_not_exact_type(self):
        pages = Page.objects.not_exact_type(EventPage)

        # Check that no objects are EventPages
        for page in pages:
            self.assertNotEqual(type(page.specific), EventPage)

        # Check that the homepage is in the results
        homepage = Page.objects.get(url_path='/home/')
        self.assertTrue(pages.filter(id=homepage.id).exists())

        # Check that "Saint Patrick" (an instance of SingleEventPage, a subclass of EventPage)
        # is in the results
        event = Page.objects.get(url_path='/home/events/saint-patrick/')
        self.assertTrue(pages.filter(id=event.id).exists())

    def test_public(self):
        events_index = Page.objects.get(url_path='/home/events/')
        event = Page.objects.get(url_path='/home/events/christmas/')
        homepage = Page.objects.get(url_path='/home/')

        # Add PageViewRestriction to events_index
        PageViewRestriction.objects.create(page=events_index, password='hello')

        # Get public pages
        pages = Page.objects.public()

        # Check that the homepage is in the results
        self.assertTrue(pages.filter(id=homepage.id).exists())

        # Check that the events index is not in the results
        self.assertFalse(pages.filter(id=events_index.id).exists())

        # Check that the event is not in the results
        self.assertFalse(pages.filter(id=event.id).exists())

    def test_not_public(self):
        events_index = Page.objects.get(url_path='/home/events/')
        event = Page.objects.get(url_path='/home/events/christmas/')
        homepage = Page.objects.get(url_path='/home/')

        # Add PageViewRestriction to events_index
        PageViewRestriction.objects.create(page=events_index, password='hello')

        # Get public pages
        pages = Page.objects.not_public()

        # Check that the homepage is not in the results
        self.assertFalse(pages.filter(id=homepage.id).exists())

        # Check that the events index is in the results
        self.assertTrue(pages.filter(id=events_index.id).exists())

        # Check that the event is in the results
        self.assertTrue(pages.filter(id=event.id).exists())


class TestPageQuerySetSearch(TestCase):
    fixtures = ['test.json']

    def test_search(self):
        pages = EventPage.objects.search('moon', fields=['location'])

        self.assertEqual(pages.count(), 2)
        self.assertIn(Page.objects.get(url_path='/home/events/tentative-unpublished-event/').specific, pages)
        self.assertIn(Page.objects.get(url_path='/home/events/someone-elses-event/').specific, pages)

    def test_operators(self):
        results = EventPage.objects.search("moon ponies", operator='and')

        self.assertEqual(list(results), [
            Page.objects.get(url_path='/home/events/tentative-unpublished-event/').specific
        ])

        results = EventPage.objects.search("moon ponies", operator='or')
        sorted_results = sorted(results, key=lambda page: page.url_path)
        self.assertEqual(sorted_results, [
            Page.objects.get(url_path='/home/events/someone-elses-event/').specific,
            Page.objects.get(url_path='/home/events/tentative-unpublished-event/').specific,
        ])

    def test_custom_order(self):
        pages = EventPage.objects.order_by('url_path').search('moon', fields=['location'], order_by_relevance=False)

        self.assertEqual(list(pages), [
            Page.objects.get(url_path='/home/events/someone-elses-event/').specific,
            Page.objects.get(url_path='/home/events/tentative-unpublished-event/').specific,
        ])

        pages = EventPage.objects.order_by('-url_path').search('moon', fields=['location'], order_by_relevance=False)

        self.assertEqual(list(pages), [
            Page.objects.get(url_path='/home/events/tentative-unpublished-event/').specific,
            Page.objects.get(url_path='/home/events/someone-elses-event/').specific,
        ])

    def test_unpublish(self):
        # set up a listener for the unpublish signal
        unpublish_signals_fired = []

        def page_unpublished_handler(sender, instance, **kwargs):
            unpublish_signals_fired.append((sender, instance))

        page_unpublished.connect(page_unpublished_handler)

        events_index = Page.objects.get(url_path='/home/events/')
        events_index.get_children().unpublish()

        # Previously-live children of event index should now be non-live
        christmas = EventPage.objects.get(url_path='/home/events/christmas/')
        saint_patrick = SingleEventPage.objects.get(url_path='/home/events/saint-patrick/')
        unpublished_event = EventPage.objects.get(url_path='/home/events/tentative-unpublished-event/')

        self.assertFalse(christmas.live)
        self.assertFalse(saint_patrick.live)

        # Check that a signal was fired for each unpublished page
        self.assertIn((EventPage, christmas), unpublish_signals_fired)
        self.assertIn((SingleEventPage, saint_patrick), unpublish_signals_fired)

        # a signal should not be fired for pages that were in the queryset
        # but already unpublished
        self.assertNotIn((EventPage, unpublished_event), unpublish_signals_fired)


class TestSpecificQuery(TestCase):
    """
    Test the .specific() queryset method. This is isolated in its own test case
    because it is sensitive to database changes that might happen for other
    tests.

    The fixture sets up a page structure like:

    =========== =========================================
    Type        Path
    =========== =========================================
    Page        /
    Page        /home/
    SimplePage  /home/about-us/
    EventIndex  /home/events/
    EventPage   /home/events/christmas/
    EventPage   /home/events/someone-elses-event/
    EventPage   /home/events/tentative-unpublished-event/
    SimplePage  /home/other/
    EventPage   /home/other/special-event/
    =========== =========================================
    """

    fixtures = ['test_specific.json']

    def test_specific(self):
        root = Page.objects.get(url_path='/home/')

        with self.assertNumQueries(0):
            # The query should be lazy.
            qs = root.get_descendants().specific()

        with self.assertNumQueries(4):
            # One query to get page type and ID, one query per page type:
            # EventIndex, EventPage, SimplePage
            pages = list(qs)

        self.assertIsInstance(pages, list)
        self.assertEqual(len(pages), 7)

        for page in pages:
            # An instance of the specific page type should be returned,
            # not wagtailcore.Page.
            content_type = page.content_type
            model = content_type.model_class()
            self.assertIsInstance(page, model)

            # The page should already be the specific type, so this should not
            # need another database query.
            with self.assertNumQueries(0):
                self.assertIs(page, page.specific)

    def test_filtering_before_specific(self):
        # This will get the other events, and then christmas
        # 'someone-elses-event' and the tentative event are unpublished.

        with self.assertNumQueries(0):
            qs = Page.objects.live().order_by('-url_path')[:3].specific()

        with self.assertNumQueries(3):
            # Metadata, EventIndex and EventPage
            pages = list(qs)

        self.assertEqual(len(pages), 3)

        self.assertEqual(pages, [
            Page.objects.get(url_path='/home/other/special-event/').specific,
            Page.objects.get(url_path='/home/other/').specific,
            Page.objects.get(url_path='/home/events/christmas/').specific])

    def test_filtering_after_specific(self):
        # This will get the other events, and then christmas
        # 'someone-elses-event' and the tentative event are unpublished.

        with self.assertNumQueries(0):
            qs = Page.objects.specific().live().in_menu().order_by('-url_path')[:4]

        with self.assertNumQueries(4):
            # Metadata, EventIndex, EventPage, SimplePage.
            pages = list(qs)

        self.assertEqual(len(pages), 4)

        self.assertEqual(pages, [
            Page.objects.get(url_path='/home/other/').specific,
            Page.objects.get(url_path='/home/events/christmas/').specific,
            Page.objects.get(url_path='/home/events/').specific,
            Page.objects.get(url_path='/home/about-us/').specific])

    def test_specific_query_with_search(self):
        # 1276 - The database search backend didn't return results with the
        # specific type when searching a specific queryset.

        pages = list(Page.objects.specific().live().in_menu().search(None, backend='wagtail.wagtailsearch.backends.db'))

        # Check that each page is in the queryset with the correct type.
        # We don't care about order here
        self.assertEqual(len(pages), 4)
        self.assertIn(Page.objects.get(url_path='/home/other/').specific, pages)
        self.assertIn(Page.objects.get(url_path='/home/events/christmas/').specific, pages)
        self.assertIn(Page.objects.get(url_path='/home/events/').specific, pages)
        self.assertIn(Page.objects.get(url_path='/home/about-us/').specific, pages)
