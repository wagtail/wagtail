from unittest import mock

from django.db import connection
from django.test import TestCase

from wagtail.core.models import Site
from wagtail.core.signals import page_url_path_changed
from wagtail.tests.testapp.models import SimplePage
from wagtail.tests.utils import WagtailTestUtils


class TestPageURLPathChangedSignal(TestCase, WagtailTestUtils):
    """
    Tests for the `wagtail.core.signals.page_url_path_changed` signal
    """

    def setUp(self):
        # Find root page
        site = Site.objects.select_related('root_page').get(is_default_site=True)
        root_page = site.root_page

        # Create two sections
        self.section_a = SimplePage(title="Section A", slug="section-a", content="hello")
        root_page.add_child(instance=self.section_a)

        self.section_b = SimplePage(title="Section B", slug="section-b", content="hello")
        root_page.add_child(instance=self.section_b)

        # Add test pages to section A
        self.test_page = SimplePage(title="Hello world! A", slug="hello-world-a", content="hello")
        self.section_a.add_child(instance=self.test_page)

    def test_signal_emitted_on_slug_change(self):
        # Connect a mock signal handler to the signal
        handler = mock.MagicMock()
        page_url_path_changed.connect(handler)

        try:
            self.test_page.slug = 'updated'
            self.test_page.save()
            # TODO: When Django 3.1< support is dropped, wrap save in
            # self.captureOnCommitCallbacks and remove this code
            for _, func in connection.run_on_commit:
                func()
        finally:
            # Disconnect mock handler to prevent cross-test pollution
            page_url_path_changed.disconnect(handler)

        # Check the signal was fired
        self.assertEqual(handler.call_count, 1)
        self.assertTrue(
            handler.called_with(
                sender=SimplePage,
                instance=self.test_page,
                url_path_before='/home/section-a/hello-world-a/',
                url_path_after='/home/section-a/updated/',
                log_entry=mock.ANY,
            )
        )

    def test_signal_emitted_on_page_move(self):
        # Connect a mock signal handler to the signal
        handler = mock.MagicMock()
        page_url_path_changed.connect(handler)

        try:
            self.test_page.move(self.section_b, pos="last-child")
        finally:
            # Disconnect mock handler to prevent cross-test pollution
            page_url_path_changed.disconnect(handler)

        # Check the signal was fired
        self.assertEqual(handler.call_count, 1)
        self.assertTrue(
            handler.called_with(
                sender=SimplePage,
                instance=self.test_page,
                url_path_before='/home/section-a/hello-world-a/',
                url_path_after='/home/section-b/hello-world-a/',
                log_entry=mock.ANY,
            )
        )

    def test_signal_not_emitted_on_title_change(self):
        # Connect a mock signal handler to the signal
        handler = mock.MagicMock()
        page_url_path_changed.connect(handler)

        try:
            self.test_page.title = 'Goodnight Moon!'
            self.test_page.save()
            # NOTE: Even though we're not expecting anything to happen here,
            # we need to invoke the callbacks in run_on_commit the same way
            # the same way we do in ``test_signal_emitted_on_slug_change``,
            # otherwise this test wouldn't prove anything.
            for _, func in connection.run_on_commit:
                func()
        finally:
            # Disconnect mock handler to prevent cross-test pollution
            page_url_path_changed.disconnect(handler)

        # Check the signal was NOT fired
        self.assertEqual(handler.call_count, 0)

    def test_signal_not_emitted_when_reordering(self):
        # Add a couple of siblings for the test page to make reording more apparent
        self.section_a.add_child(instance=SimplePage(title="Sibling 1", slug="sibling-one", content="foo"))
        self.section_a.add_child(instance=SimplePage(title="Sibling 2", slug="sibling-two", content="foo"))

        # Connect a mock signal handler to the signal
        handler = mock.MagicMock()
        page_url_path_changed.connect(handler)

        try:
            # Move 'test_page' from first to last place (under the same parent)
            self.test_page.move(self.test_page.get_parent(), pos="last-child")
            self.test_page.save()
        finally:
            # Disconnect mock handler to prevent cross-test pollution
            page_url_path_changed.disconnect(handler)

        # Check the signal was NOT fired
        self.assertEqual(handler.call_count, 0)
