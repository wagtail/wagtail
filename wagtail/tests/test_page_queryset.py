from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core import management
from django.db.models import Count, Q
from django.test import TestCase, TransactionTestCase

from wagtail.models import Locale, Page, PageViewRestriction, Site, Workflow
from wagtail.search.query import MATCH_ALL
from wagtail.signals import page_unpublished
from wagtail.test.testapp.models import (
    EventPage,
    SimplePage,
    SingleEventPage,
    StreamPage,
)
from wagtail.test.utils import WagtailTestUtils


class TestPageQuerySet(TestCase):
    fixtures = ["test.json"]

    def test_live(self):
        pages = Page.objects.live()

        # All pages must be live
        for page in pages:
            self.assertTrue(page.live)

        # Check that the homepage is in the results
        homepage = Page.objects.get(url_path="/home/")
        self.assertTrue(pages.filter(id=homepage.id).exists())

    def test_not_live(self):
        pages = Page.objects.not_live()

        # All pages must not be live
        for page in pages:
            self.assertFalse(page.live)

        # Check that "someone elses event" is in the results
        event = Page.objects.get(url_path="/home/events/someone-elses-event/")
        self.assertTrue(pages.filter(id=event.id).exists())

    def test_in_menu(self):
        pages = Page.objects.in_menu()

        # All pages must be be in the menus
        for page in pages:
            self.assertTrue(page.show_in_menus)

        # Check that the events index is in the results
        events_index = Page.objects.get(url_path="/home/events/")
        self.assertTrue(pages.filter(id=events_index.id).exists())

    def test_not_in_menu(self):
        pages = Page.objects.not_in_menu()

        # All pages must not be in menus
        for page in pages:
            self.assertFalse(page.show_in_menus)

        # Check that the root page is in the results
        self.assertTrue(pages.filter(id=1).exists())

    def test_page(self):
        homepage = Page.objects.get(url_path="/home/")
        pages = Page.objects.page(homepage)

        # Should only select the homepage
        self.assertEqual(pages.count(), 1)
        self.assertEqual(pages.first(), homepage)

    def test_not_page(self):
        homepage = Page.objects.get(url_path="/home/")
        pages = Page.objects.not_page(homepage)

        # Should select everything except for the homepage
        self.assertEqual(pages.count(), Page.objects.all().count() - 1)
        for page in pages:
            self.assertNotEqual(page, homepage)

    def test_descendant_of(self):
        events_index = Page.objects.get(url_path="/home/events/")
        pages = Page.objects.descendant_of(events_index)

        # Check that all pages descend from events index
        for page in pages:
            self.assertTrue(page.get_ancestors().filter(id=events_index.id).exists())

    def test_descendant_of_inclusive(self):
        events_index = Page.objects.get(url_path="/home/events/")
        pages = Page.objects.descendant_of(events_index, inclusive=True)

        # Check that all pages descend from events index, includes event index
        for page in pages:
            self.assertTrue(
                page == events_index
                or page.get_ancestors().filter(id=events_index.id).exists()
            )

        # Check that event index was included
        self.assertTrue(pages.filter(id=events_index.id).exists())

    def test_not_descendant_of(self):
        events_index = Page.objects.get(url_path="/home/events/")
        pages = Page.objects.not_descendant_of(events_index)

        # Check that no pages descend from events_index
        for page in pages:
            self.assertFalse(page.get_ancestors().filter(id=events_index.id).exists())

        # As this is not inclusive, events index should be in the results
        self.assertTrue(pages.filter(id=events_index.id).exists())

    def test_not_descendant_of_inclusive(self):
        events_index = Page.objects.get(url_path="/home/events/")
        pages = Page.objects.not_descendant_of(events_index, inclusive=True)

        # Check that all pages descend from homepage but not events index
        for page in pages:
            self.assertFalse(page.get_ancestors().filter(id=events_index.id).exists())

        # As this is inclusive, events index should not be in the results
        self.assertFalse(pages.filter(id=events_index.id).exists())

    def test_child_of(self):
        homepage = Page.objects.get(url_path="/home/")
        pages = Page.objects.child_of(homepage)

        # Check that all pages are children of homepage
        for page in pages:
            self.assertEqual(page.get_parent(), homepage)

    def test_not_child_of(self):
        events_index = Page.objects.get(url_path="/home/events/")
        pages = Page.objects.not_child_of(events_index)

        # Check that all pages are not children of events_index
        for page in pages:
            self.assertNotEqual(page.get_parent(), events_index)

    def test_ancestor_of(self):
        root_page = Page.objects.get(id=1)
        homepage = Page.objects.get(url_path="/home/")
        events_index = Page.objects.get(url_path="/home/events/")
        pages = Page.objects.ancestor_of(events_index)

        self.assertEqual(pages.count(), 2)
        self.assertEqual(pages[0], root_page)
        self.assertEqual(pages[1], homepage)

    def test_ancestor_of_inclusive(self):
        root_page = Page.objects.get(id=1)
        homepage = Page.objects.get(url_path="/home/")
        events_index = Page.objects.get(url_path="/home/events/")
        pages = Page.objects.ancestor_of(events_index, inclusive=True)

        self.assertEqual(pages.count(), 3)
        self.assertEqual(pages[0], root_page)
        self.assertEqual(pages[1], homepage)
        self.assertEqual(pages[2], events_index)

    def test_not_ancestor_of(self):
        root_page = Page.objects.get(id=1)
        homepage = Page.objects.get(url_path="/home/")
        events_index = Page.objects.get(url_path="/home/events/")
        pages = Page.objects.not_ancestor_of(events_index)

        # Test that none of the ancestors are in pages
        for page in pages:
            self.assertNotEqual(page, root_page)
            self.assertNotEqual(page, homepage)

        # Test that events index is in pages
        self.assertTrue(pages.filter(id=events_index.id).exists())

    def test_not_ancestor_of_inclusive(self):
        root_page = Page.objects.get(id=1)
        homepage = Page.objects.get(url_path="/home/")
        events_index = Page.objects.get(url_path="/home/events/")
        pages = Page.objects.not_ancestor_of(events_index, inclusive=True)

        # Test that none of the ancestors or the events_index are in pages
        for page in pages:
            self.assertNotEqual(page, root_page)
            self.assertNotEqual(page, homepage)
            self.assertNotEqual(page, events_index)

    def test_parent_of(self):
        homepage = Page.objects.get(url_path="/home/")
        events_index = Page.objects.get(url_path="/home/events/")
        pages = Page.objects.parent_of(events_index)

        # Pages must only contain homepage
        self.assertEqual(pages.count(), 1)
        self.assertEqual(pages[0], homepage)

    def test_not_parent_of(self):
        homepage = Page.objects.get(url_path="/home/")
        events_index = Page.objects.get(url_path="/home/events/")
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
        events_index = Page.objects.get(url_path="/home/events/")
        event = Page.objects.get(url_path="/home/events/christmas/")
        pages = Page.objects.sibling_of(event)

        # Check that all pages are children of events_index
        for page in pages:
            self.assertEqual(page.get_parent(), events_index)

        # Check that the event is included
        self.assertTrue(pages.filter(id=event.id).exists())

    def test_sibling_of_exclusive(self):
        events_index = Page.objects.get(url_path="/home/events/")
        event = Page.objects.get(url_path="/home/events/christmas/")
        pages = Page.objects.sibling_of(event, inclusive=False)

        # Check that all pages are children of events_index
        for page in pages:
            self.assertEqual(page.get_parent(), events_index)

        # Check that the event is not included
        self.assertFalse(pages.filter(id=event.id).exists())

    def test_sibling_of_inclusive(self):
        events_index = Page.objects.get(url_path="/home/events/")
        event = Page.objects.get(url_path="/home/events/christmas/")
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
        events_index = Page.objects.get(url_path="/home/events/")
        event = Page.objects.get(url_path="/home/events/christmas/")
        pages = Page.objects.not_sibling_of(event)

        # Check that all pages are not children of events_index
        for page in pages:
            self.assertNotEqual(page.get_parent(), events_index)

        # Check that the event is not included
        self.assertFalse(pages.filter(id=event.id).exists())

        # Test that events index is in pages
        self.assertTrue(pages.filter(id=events_index.id).exists())

    def test_not_sibling_of_exclusive(self):
        events_index = Page.objects.get(url_path="/home/events/")
        event = Page.objects.get(url_path="/home/events/christmas/")
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
        events_index = Page.objects.get(url_path="/home/events/")
        event = Page.objects.get(url_path="/home/events/christmas/")
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
        event = Page.objects.get(url_path="/home/events/someone-elses-event/")
        self.assertIn(event, pages)

        # Check that "Saint Patrick" (an instance of SingleEventPage, a subclass of EventPage)
        # is in the results
        event = Page.objects.get(url_path="/home/events/saint-patrick/")
        self.assertIn(event, pages)

    def test_type_with_multiple_models(self):
        pages = Page.objects.type(EventPage, SimplePage)

        # Check that all objects are EventPages or SimplePages
        for page in pages:
            self.assertIsInstance(page.specific, (EventPage, SimplePage))

        # Check that "someone elses event" is in the results
        event = Page.objects.get(url_path="/home/events/someone-elses-event/")
        self.assertIn(event, pages)

        # Check that "Saint Patrick" (an instance of SingleEventPage, a subclass of EventPage)
        # is in the results
        event = Page.objects.get(url_path="/home/events/saint-patrick/")
        self.assertIn(event, pages)

        # Check that "About us" (an instance of SimplePage) is in the results
        about_us = Page.objects.get(url_path="/home/about-us/")
        self.assertIn(about_us, pages)

    def test_not_type(self):
        pages = Page.objects.not_type(EventPage)

        # Check that no objects are EventPages
        for page in pages:
            self.assertNotIsInstance(page.specific, EventPage)

        # Check that "About us" is in the results
        about_us = Page.objects.get(url_path="/home/about-us/")
        self.assertIn(about_us, pages)

        # Check that the homepage is in the results
        homepage = Page.objects.get(url_path="/home/")
        self.assertIn(homepage, pages)

    def test_not_type_with_multiple_models(self):
        pages = Page.objects.not_type(EventPage, SimplePage)

        # Check that no objects are EventPages or SimplePages
        for page in pages:
            self.assertNotIsInstance(page.specific, (EventPage, SimplePage))

        # Check that "About us" is NOT in the results
        about_us = Page.objects.get(url_path="/home/about-us/")
        self.assertNotIn(about_us, pages)

        # Check that the homepage IS in the results
        homepage = Page.objects.get(url_path="/home/")
        self.assertIn(homepage, pages)

    def test_exact_type(self):
        pages = Page.objects.exact_type(EventPage)

        # Check that all objects are EventPages (and not a subclass)
        for page in pages:
            self.assertIs(page.specific_class, EventPage)

        # Check that "someone elses event" is in the results
        event = Page.objects.get(url_path="/home/events/someone-elses-event/")
        self.assertIn(event, pages)

        # Check that "Saint Patrick" (an instance of SingleEventPage, a subclass of EventPage)
        # is NOT in the results
        single_event = Page.objects.get(url_path="/home/events/saint-patrick/")
        self.assertNotIn(single_event, pages)

    def test_exact_type_with_multiple_models(self):
        pages = Page.objects.exact_type(EventPage, Page)

        # Check that all objects are EventPages or Pages (and not a subclass)
        for page in pages:
            self.assertIn(page.specific_class, (EventPage, Page))

        # Check that "someone elses event" is in the results
        event = Page.objects.get(url_path="/home/events/someone-elses-event/")
        self.assertIn(event, pages)

        # Check that "Saint Patrick" (an instance of SingleEventPage, a subclass of EventPage
        # and Page) is NOT in the results
        single_event = Page.objects.get(url_path="/home/events/saint-patrick/")
        self.assertNotIn(single_event, pages)

        # Check that the homepage (a generic Page only) is in the results
        homepage = Page.objects.get(url_path="/home/")
        self.assertIn(homepage, pages)

        # Check that "About us" (an instance of SimplePage, a subclass of Page)
        # is NOT in the results
        about_us = Page.objects.get(url_path="/home/about-us/")
        self.assertNotIn(about_us, pages)

    def test_not_exact_type(self):
        pages = Page.objects.not_exact_type(EventPage)

        # Check that no objects are EventPages
        for page in pages:
            self.assertIsNot(page.specific_class, EventPage)

        # Check that the homepage is in the results
        homepage = Page.objects.get(url_path="/home/")
        self.assertIn(homepage, pages)

        # Check that "Saint Patrick" (an instance of SingleEventPage, a subclass of EventPage)
        # is in the results
        event = Page.objects.get(url_path="/home/events/saint-patrick/")
        self.assertIn(event, pages)

    def test_not_exact_type_with_multiple_models(self):
        pages = Page.objects.not_exact_type(EventPage, Page)

        # Check that no objects are EventPages or generic Pages
        for page in pages:
            self.assertNotIn(page.specific_class, (EventPage, Page))

        # Check that "Saint Patrick" (an instance of SingleEventPage, a subclass of EventPage)
        # is in the results
        event = Page.objects.get(url_path="/home/events/saint-patrick/")
        self.assertIn(event, pages)

        # Check that "About us" (an instance of SimplePage, a subclass of Page)
        # is in the results
        about_us = Page.objects.get(url_path="/home/about-us/")
        self.assertIn(about_us, pages)

    def test_public(self):
        events_index = Page.objects.get(url_path="/home/events/")
        event = Page.objects.get(url_path="/home/events/christmas/")
        homepage = Page.objects.get(url_path="/home/")

        # Add PageViewRestriction to events_index
        PageViewRestriction.objects.create(page=events_index, password="hello")

        with self.assertNumQueries(4):
            # Get public pages
            pages = Page.objects.public()

            # Check that the homepage is in the results
            self.assertTrue(pages.filter(id=homepage.id).exists())

            # Check that the events index is not in the results
            self.assertFalse(pages.filter(id=events_index.id).exists())

            # Check that the event is not in the results
            self.assertFalse(pages.filter(id=event.id).exists())

    def test_not_public(self):
        events_index = Page.objects.get(url_path="/home/events/")
        event = Page.objects.get(url_path="/home/events/christmas/")
        homepage = Page.objects.get(url_path="/home/")

        # Add PageViewRestriction to events_index
        PageViewRestriction.objects.create(page=events_index, password="hello")

        with self.assertNumQueries(4):
            # Get public pages
            pages = Page.objects.not_public()

            # Check that the homepage is not in the results
            self.assertFalse(pages.filter(id=homepage.id).exists())

            # Check that the events index is in the results
            self.assertTrue(pages.filter(id=events_index.id).exists())

            # Check that the event is in the results
            self.assertTrue(pages.filter(id=event.id).exists())

    def test_private(self):
        events_index = Page.objects.get(url_path="/home/events/")
        event = Page.objects.get(url_path="/home/events/christmas/")
        homepage = Page.objects.get(url_path="/home/")

        # Add PageViewRestriction to events_index
        PageViewRestriction.objects.create(page=events_index, password="hello")

        with self.assertNumQueries(4):
            # Get public pages
            pages = Page.objects.private()

            # Check that the homepage is not in the results
            self.assertFalse(pages.filter(id=homepage.id).exists())

            # Check that the events index is in the results
            self.assertTrue(pages.filter(id=events_index.id).exists())

            # Check that the event is in the results
            self.assertTrue(pages.filter(id=event.id).exists())

    def test_private_with_no_private_page(self):
        PageViewRestriction.objects.all().delete()

        count = Page.objects.private().count()
        self.assertEqual(count, 0)

    def test_merge_queries(self):
        type_q = Page.objects.type_q(EventPage)
        query = Q()

        query |= type_q

        self.assertTrue(Page.objects.filter(query).exists())

    def test_delete_queryset(self):
        Page.objects.all().delete()
        self.assertEqual(Page.objects.count(), 0)

    def test_delete_is_not_available_on_manager(self):
        with self.assertRaises(AttributeError):
            Page.objects.delete()

    def test_translation_of(self):
        en_homepage = Page.objects.get(url_path="/home/")

        # Create a translation of the homepage
        fr_locale = Locale.objects.create(language_code="fr")
        root_page = Page.objects.get(depth=1)
        fr_homepage = root_page.add_child(
            instance=Page(
                title="French homepage",
                slug="home-fr",
                locale=fr_locale,
                translation_key=en_homepage.translation_key,
            )
        )

        with self.assertNumQueries(1):
            translations = Page.objects.translation_of(en_homepage)
            self.assertListEqual(list(translations), [fr_homepage])

        # Now test with inclusive
        with self.assertNumQueries(1):
            translations = Page.objects.translation_of(
                en_homepage, inclusive=True
            ).order_by("id")
            self.assertListEqual(list(translations), [en_homepage, fr_homepage])

    def test_not_translation_of(self):
        en_homepage = Page.objects.get(url_path="/home/")

        # Create a translation of the homepage
        fr_locale = Locale.objects.create(language_code="fr")
        root_page = Page.objects.get(depth=1)
        fr_homepage = root_page.add_child(
            instance=Page(
                title="French homepage",
                slug="home-fr",
                locale=fr_locale,
                translation_key=en_homepage.translation_key,
            )
        )

        with self.assertNumQueries(1):
            translations = list(Page.objects.not_translation_of(en_homepage))

        # Check that every single page is in the queryset, except for fr_homepage
        for page in Page.objects.all():
            if page in [fr_homepage]:
                self.assertNotIn(page, translations)
            else:
                self.assertIn(page, translations)

        # Test with inclusive
        with self.assertNumQueries(1):
            translations = list(
                Page.objects.not_translation_of(en_homepage, inclusive=True)
            )

        # Check that every single page is in the queryset, except for fr_homepage and en_homepage
        for page in Page.objects.all():
            if page in [en_homepage, fr_homepage]:
                self.assertNotIn(page, translations)
            else:
                self.assertIn(page, translations)

    def test_prefetch_workflow_states(self):
        home = Page.objects.get(url_path="/home/")
        event_index = Page.objects.get(url_path="/home/events/")
        user = get_user_model().objects.first()
        workflow = Workflow.objects.first()

        test_pages = [home.specific, event_index.specific]
        workflow_states = {}
        current_tasks = {}

        for page in test_pages:
            page.save_revision()
            approved_workflow_state = workflow.start(page, user)
            task_state = approved_workflow_state.current_task_state
            task_state.task.on_action(task_state, user=None, action_name="approve")

            workflow_state = workflow.start(page, user)

            # Refresh so that the current_task_state.task is not the specific instance
            workflow_state.refresh_from_db()

            workflow_states[page.pk] = workflow_state
            current_tasks[page.pk] = workflow_state.current_task_state.task

        query = Page.objects.filter(pk__in=(home.pk, event_index.pk))
        queries = [["base", query, 2], ["specific", query.specific(), 4]]

        for case, query, num_queries in queries:
            with self.subTest(case=case):
                with self.assertNumQueries(num_queries):
                    queried_pages = {
                        page.pk: page for page in query.prefetch_workflow_states()
                    }

                for test_page in test_pages:
                    page = queried_pages[test_page.pk]
                    with self.assertNumQueries(0):
                        self.assertEqual(
                            page._current_workflow_states,
                            [workflow_states[page.pk]],
                        )

                    with self.assertNumQueries(0):
                        self.assertEqual(
                            page._current_workflow_states[0].current_task_state.task,
                            current_tasks[page.pk],
                        )

                    with self.assertNumQueries(0):
                        self.assertTrue(page.workflow_in_progress)

                    with self.assertNumQueries(0):
                        self.assertTrue(
                            page.current_workflow_state,
                            workflow_states[page.pk],
                        )


class TestPageQueryInSite(TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.site_2_page = SimplePage(
            title="Site 2 page",
            slug="site_2_page",
            content="Hello",
        )
        Page.get_first_root_node().add_child(instance=self.site_2_page)
        self.site_2_subpage = SimplePage(
            title="Site 2 subpage",
            slug="site_2_subpage",
            content="Hello again",
        )
        self.site_2_page.add_child(instance=self.site_2_subpage)

        self.site_2 = Site.objects.create(
            hostname="example.com",
            port=8080,
            root_page=Page.objects.get(pk=self.site_2_page.pk),
            is_default_site=False,
        )
        self.about_us_page = SimplePage.objects.get(url_path="/home/about-us/")

    def test_in_site(self):
        site_2_pages = SimplePage.objects.in_site(self.site_2)

        self.assertIn(self.site_2_page, site_2_pages)
        self.assertIn(self.site_2_subpage, site_2_pages)
        self.assertNotIn(self.about_us_page, site_2_pages)


class TestPageQuerySetSearch(TransactionTestCase):
    fixtures = ["test.json"]

    def test_search(self):
        pages = EventPage.objects.search("moon", fields=["location"])

        self.assertEqual(pages.count(), 2)
        self.assertIn(
            Page.objects.get(
                url_path="/home/events/tentative-unpublished-event/"
            ).specific,
            pages,
        )
        self.assertIn(
            Page.objects.get(url_path="/home/events/someone-elses-event/").specific,
            pages,
        )

    def test_operators(self):
        results = EventPage.objects.search("moon ponies", operator="and")

        self.assertEqual(
            list(results),
            [
                Page.objects.get(
                    url_path="/home/events/tentative-unpublished-event/"
                ).specific
            ],
        )

        results = EventPage.objects.search("moon ponies", operator="or")
        sorted_results = sorted(results, key=lambda page: page.url_path)
        self.assertEqual(
            sorted_results,
            [
                Page.objects.get(url_path="/home/events/someone-elses-event/").specific,
                Page.objects.get(
                    url_path="/home/events/tentative-unpublished-event/"
                ).specific,
            ],
        )

    def test_custom_order(self):
        pages = EventPage.objects.order_by("url_path").search(
            "moon", fields=["location"], order_by_relevance=False
        )

        self.assertEqual(
            list(pages),
            [
                Page.objects.get(url_path="/home/events/someone-elses-event/").specific,
                Page.objects.get(
                    url_path="/home/events/tentative-unpublished-event/"
                ).specific,
            ],
        )

        pages = EventPage.objects.order_by("-url_path").search(
            "moon", fields=["location"], order_by_relevance=False
        )

        self.assertEqual(
            list(pages),
            [
                Page.objects.get(
                    url_path="/home/events/tentative-unpublished-event/"
                ).specific,
                Page.objects.get(url_path="/home/events/someone-elses-event/").specific,
            ],
        )

    def test_unpublish(self):
        # set up a listener for the unpublish signal
        unpublish_signals_fired = []

        def page_unpublished_handler(sender, instance, **kwargs):
            unpublish_signals_fired.append((sender, instance))

        page_unpublished.connect(page_unpublished_handler)

        try:
            events_index = Page.objects.get(url_path="/home/events/")
            events_index.get_children().unpublish()

            # Previously-live children of event index should now be non-live
            christmas = EventPage.objects.get(url_path="/home/events/christmas/")
            saint_patrick = SingleEventPage.objects.get(
                url_path="/home/events/saint-patrick/"
            )
            unpublished_event = EventPage.objects.get(
                url_path="/home/events/tentative-unpublished-event/"
            )

            self.assertFalse(christmas.live)
            self.assertFalse(saint_patrick.live)

            # Check that a signal was fired for each unpublished page
            self.assertIn((EventPage, christmas), unpublish_signals_fired)
            self.assertIn((SingleEventPage, saint_patrick), unpublish_signals_fired)

            # a signal should not be fired for pages that were in the queryset
            # but already unpublished
            self.assertNotIn((EventPage, unpublished_event), unpublish_signals_fired)
        finally:
            page_unpublished.disconnect(page_unpublished_handler)


class TestSpecificQuery(WagtailTestUtils, TestCase):
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

    fixtures = ["test_specific.json"]

    def setUp(self):
        self.live_pages = Page.objects.live().specific()
        self.live_pages_with_annotations = (
            Page.objects.live().specific().annotate(count=Count("pk"))
        )

    def test_specific(self):
        root = Page.objects.get(url_path="/home/")

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
            qs = Page.objects.live().order_by("-url_path")[:3].specific()

        with self.assertNumQueries(3):
            # Metadata, EventIndex and EventPage
            pages = list(qs)

        self.assertEqual(len(pages), 3)

        self.assertEqual(
            pages,
            [
                Page.objects.get(url_path="/home/other/special-event/").specific,
                Page.objects.get(url_path="/home/other/").specific,
                Page.objects.get(url_path="/home/events/christmas/").specific,
            ],
        )

    def test_filtering_after_specific(self):
        # This will get the other events, and then christmas
        # 'someone-elses-event' and the tentative event are unpublished.

        with self.assertNumQueries(0):
            qs = Page.objects.specific().live().in_menu().order_by("-url_path")[:4]

        with self.assertNumQueries(4):
            # Metadata, EventIndex, EventPage, SimplePage.
            pages = list(qs)

        self.assertEqual(len(pages), 4)

        self.assertEqual(
            pages,
            [
                Page.objects.get(url_path="/home/other/").specific,
                Page.objects.get(url_path="/home/events/christmas/").specific,
                Page.objects.get(url_path="/home/events/").specific,
                Page.objects.get(url_path="/home/about-us/").specific,
            ],
        )

    def test_specific_query_with_annotations_performs_no_additional_queries(self):

        with self.assertNumQueries(5):
            pages = list(self.live_pages)

            self.assertEqual(len(pages), 7)

        with self.assertNumQueries(5):
            pages = list(self.live_pages_with_annotations)

            self.assertEqual(len(pages), 7)

    def test_specific_query_with_annotation(self):
        # Ensure annotations are reapplied to specific() page queries

        pages = Page.objects.live()
        user = self.create_test_user()
        pages.first().subscribers.create(user=user, comment_notifications=False)
        pages.last().subscribers.create(user=user, comment_notifications=False)

        results = (
            Page.objects.live()
            .specific()
            .annotate(subscribers_count=Count("subscribers"))
        )

        self.assertEqual(results.first().subscribers_count, 1)
        self.assertEqual(results.last().subscribers_count, 1)

    def test_specific_query_with_alias(self):
        """
        Ensure alias() works with specific() queries.
        See https://github.com/wagtail/wagtail/issues/11285 for more details
        """

        pages = Page.objects.live()
        user = self.create_test_user()
        pages.first().subscribers.create(user=user, comment_notifications=False)
        pages.last().subscribers.create(user=user, comment_notifications=False)

        # This would previously fail as described in #11285.
        iter(
            Page.objects.live()
            .specific()
            .alias(subscribers_count=Count("subscribers"))
            .order_by("subscribers_count")
        )

    def test_specific_gracefully_handles_missing_models(self):
        # 3567 - PageQuerySet.specific should gracefully handle pages whose class definition
        # is missing, by keeping them as basic Page instances.

        # Create a ContentType that doesn't correspond to a real model
        missing_page_content_type = ContentType.objects.create(
            app_label="tests", model="missingpage"
        )
        # Turn /home/events/ into this content type
        Page.objects.filter(url_path="/home/events/").update(
            content_type=missing_page_content_type
        )

        pages = list(Page.objects.get(url_path="/home/").get_children().specific())
        self.assertEqual(
            pages,
            [
                Page.objects.get(url_path="/home/events/"),
                Page.objects.get(url_path="/home/about-us/").specific,
                Page.objects.get(url_path="/home/other/").specific,
            ],
        )

    def test_specific_gracefully_handles_missing_rows(self):
        # 5928 - PageQuerySet.specific should gracefully handle pages whose ContentType
        # row in the specific table no longer exists

        # Trick SpecificIteraterable.__init__() into always looking for EventPages
        with mock.patch(
            "wagtail.query.ContentType.objects.get_for_id",
            return_value=ContentType.objects.get_for_model(EventPage),
        ):
            with self.assertWarnsRegex(
                RuntimeWarning,
                "Specific versions of the following items could not be found",
            ):
                pages = list(
                    Page.objects.get(url_path="/home/").get_children().specific()
                )

            # All missing pages should be supplemented with generic pages
            self.assertEqual(
                pages,
                [
                    Page.objects.get(url_path="/home/events/"),
                    Page.objects.get(url_path="/home/about-us/"),
                    Page.objects.get(url_path="/home/other/"),
                ],
            )

    def test_deferred_specific_query(self):
        # Tests the "defer" keyword argument, which defers all specific fields
        root = Page.objects.get(url_path="/home/")
        stream_page = StreamPage(
            title="stream page",
            slug="stream-page",
            body='[{"type": "text", "value": "foo"}]',
        )
        root.add_child(instance=stream_page)

        with self.assertNumQueries(0):
            # The query should be lazy.
            qs = root.get_descendants().specific(defer=True)

        with self.assertNumQueries(1):
            # This did use 5 queries (one for each specific class),
            # But now only performs a single query
            pages = list(qs)

        self.assertIsInstance(pages, list)
        self.assertEqual(len(pages), 8)

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

        # Unlike before, the content fields should be now deferred. This means
        # that accessing them will generate a new query.
        with self.assertNumQueries(2):
            # <EventPage: Christmas>
            pages[1].body
            # <StreamPage: stream page>
            pages[-1].body

    def test_specific_query_with_iterator(self):
        queryset = self.live_pages_with_annotations

        # set benchmark without iterator()
        with self.assertNumQueries(5):
            benchmark_result = list(queryset.all())
            self.assertEqual(len(benchmark_result), 7)

        # the default chunk size for iterator() is much higher than 7, so all
        # items should fetched with the same number of queries
        with self.assertNumQueries(5):
            result_1 = list(queryset.all().iterator())
            self.assertEqual(result_1, benchmark_result)

        # specifying a smaller chunk_size for iterator() should force the
        # results to be processed in multiple batches, increasing the number
        # of queries
        with self.assertNumQueries(7):
            result_2 = list(queryset.all().iterator(chunk_size=5))
            self.assertEqual(result_2, benchmark_result)

        # repeat with a smaller chunk size for good measure
        with self.assertNumQueries(6):
            # The number of queries is actually lower, because
            # each chunk contains fewer 'unique' page types
            result_3 = list(queryset.all().iterator(chunk_size=2))
            self.assertEqual(result_3, benchmark_result)

    def test_bottom_sliced_specific_query_with_iterator(self):
        queryset = self.live_pages_with_annotations[2:]

        # set benchmark without iterator()
        with self.assertNumQueries(4):
            benchmark_result = list(queryset.all())
            self.assertEqual(len(benchmark_result), 5)

        # using plain iterator() with the same sliced queryset should produce
        # an identical result with the same number of queries
        with self.assertNumQueries(4):
            result_1 = list(queryset.all().iterator())
            self.assertEqual(result_1, benchmark_result)

        # if the iterator() chunk size is smaller than the slice,
        # SpecificIterable should still apply chunking whilst maintaining
        # the slice starting point
        with self.assertNumQueries(6):
            result_2 = list(queryset.all().iterator(chunk_size=1))
            self.assertEqual(result_2, benchmark_result)

    def test_top_sliced_specific_query_with_iterator(self):
        queryset = self.live_pages_with_annotations[:6]

        # set benchmark without iterator()
        with self.assertNumQueries(5):
            benchmark_result = list(queryset.all())
            self.assertEqual(len(benchmark_result), 6)

        # using plain iterator() with the same sliced queryset should produce
        # an identical result with the same number of queries
        with self.assertNumQueries(5):
            result_1 = list(queryset.all().iterator())
            self.assertEqual(result_1, benchmark_result)

        # if the iterator() chunk size is smaller than the slice,
        # SpecificIterable should still apply chunking whilst maintaining
        # the slice end point
        with self.assertNumQueries(7):
            result_2 = list(queryset.all().iterator(chunk_size=1))
            self.assertEqual(result_2, benchmark_result)

    def test_top_and_bottom_sliced_specific_query_with_iterator(self):
        queryset = self.live_pages_with_annotations[2:6]

        # set benchmark without iterator()
        with self.assertNumQueries(4):
            benchmark_result = list(queryset.all())
            self.assertEqual(len(benchmark_result), 4)

        # using plain iterator() with the same sliced queryset should produce
        # an identical result with the same number of queries
        with self.assertNumQueries(4):
            result_1 = list(queryset.all().iterator())
            self.assertEqual(result_1, benchmark_result)

        # if the iterator() chunk size is smaller than the slice,
        # SpecificIterable should still apply chunking whilst maintaining
        # the slice's start and end point
        with self.assertNumQueries(5):
            result_2 = list(queryset.all().iterator(chunk_size=3))
            self.assertEqual(result_2, benchmark_result)


class TestSpecificQuerySearch(WagtailTestUtils, TransactionTestCase):
    fixtures = ["test_specific.json"]

    def setUp(self):
        management.call_command(
            "update_index",
            backend_name="default",
            stdout=StringIO(),
            chunk_size=50,
        )

        self.live_pages = Page.objects.live().specific()
        self.live_pages_with_annotations = (
            Page.objects.live().specific().annotate(count=Count("pk"))
        )

    def test_specific_query_with_match_all_search_and_annotation(self):
        # Ensure annotations are reapplied to specific() page queries

        results = (
            Page.objects.live().specific().search(MATCH_ALL).annotate_score("_score")
        )

        self.assertGreater(len(results), 0)
        for result in results:
            self.assertTrue(hasattr(result, "_score"))

    def test_specific_query_with_real_search_and_annotation(self):
        # Ensure annotations are reapplied to specific() page queries

        results = (
            Page.objects.live().specific().search("event").annotate_score("_score")
        )

        self.assertGreater(len(results), 0)
        for result in results:
            self.assertTrue(hasattr(result, "_score"))

    def test_specific_query_with_search(self):
        # 1276 - The database search backend didn't return results with the
        # specific type when searching a specific queryset.

        pages = list(
            Page.objects.specific()
            .live()
            .in_menu()
            .search(MATCH_ALL, backend="wagtail.search.backends.database")
        )

        # Check that each page is in the queryset with the correct type.
        # We don't care about order here
        self.assertEqual(len(pages), 4)
        self.assertIn(Page.objects.get(url_path="/home/other/").specific, pages)
        self.assertIn(
            Page.objects.get(url_path="/home/events/christmas/").specific, pages
        )
        self.assertIn(Page.objects.get(url_path="/home/events/").specific, pages)
        self.assertIn(Page.objects.get(url_path="/home/about-us/").specific, pages)


class TestFirstCommonAncestor(TestCase):
    """
    Uses the same fixture as TestSpecificQuery. See that class for the layout
    of pages.
    """

    fixtures = ["test_specific.json"]

    def setUp(self):
        self.root_page = Page.objects.get(url_path="/home/")
        self.all_events = Page.objects.type(EventPage)
        self.regular_events = Page.objects.type(EventPage).exclude(
            url_path__contains="/other/"
        )

    def _create_streampage(self):
        stream_page = StreamPage(
            title="stream page",
            slug="stream-page",
            body='[{"type": "text", "value": "foo"}]',
        )
        self.root_page.add_child(instance=stream_page)

    def test_bookkeeping(self):
        self.assertEqual(self.all_events.count(), 4)
        self.assertEqual(self.regular_events.count(), 3)

    def test_event_pages(self):
        """Common ancestor for EventPages"""
        # As there are event pages in multiple trees under /home/, the home
        # page is the common ancestor
        self.assertEqual(
            Page.objects.get(slug="home"), self.all_events.first_common_ancestor()
        )

    def test_normal_event_pages(self):
        """Common ancestor for EventPages, excluding /other/ events"""
        self.assertEqual(
            Page.objects.get(slug="events"), self.regular_events.first_common_ancestor()
        )

    def test_normal_event_pages_include_self(self):
        """
        Common ancestor for EventPages, excluding /other/ events, with
        include_self=True
        """
        self.assertEqual(
            Page.objects.get(slug="events"),
            self.regular_events.first_common_ancestor(include_self=True),
        )

    def test_single_page_no_include_self(self):
        """Test getting a single page, with include_self=False."""
        self.assertEqual(
            Page.objects.get(slug="events"),
            Page.objects.filter(title="Christmas").first_common_ancestor(),
        )

    def test_single_page_include_self(self):
        """Test getting a single page, with include_self=True."""
        self.assertEqual(
            Page.objects.get(title="Christmas"),
            Page.objects.filter(title="Christmas").first_common_ancestor(
                include_self=True
            ),
        )

    def test_all_pages(self):
        self.assertEqual(
            Page.get_first_root_node(), Page.objects.first_common_ancestor()
        )

    def test_all_pages_strict(self):
        with self.assertRaises(Page.DoesNotExist):
            Page.objects.first_common_ancestor(strict=True)

    def test_all_pages_include_self_strict(self):
        self.assertEqual(
            Page.get_first_root_node(),
            Page.objects.first_common_ancestor(include_self=True, strict=True),
        )

    def test_empty_queryset(self):
        self.assertEqual(
            Page.get_first_root_node(), Page.objects.none().first_common_ancestor()
        )

    def test_empty_queryset_strict(self):
        with self.assertRaises(Page.DoesNotExist):
            Page.objects.none().first_common_ancestor(strict=True)

    def test_defer_streamfields_without_specific(self):
        self._create_streampage()
        for page in StreamPage.objects.all().defer_streamfields():
            self.assertNotIn("body", page.__dict__)
            with self.assertNumQueries(1):
                page.body

    def test_defer_streamfields_with_specific(self):
        self._create_streampage()
        for page in Page.objects.exact_type(StreamPage).defer_streamfields().specific():
            self.assertNotIn("body", page.__dict__)
            with self.assertNumQueries(1):
                page.body
