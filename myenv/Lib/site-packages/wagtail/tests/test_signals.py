from unittest import mock

from django.test import TestCase

from wagtail.models import Site
from wagtail.signals import page_slug_changed
from wagtail.test.testapp.models import SimplePage
from wagtail.test.utils import WagtailTestUtils


class TestPageSlugChangedSignal(WagtailTestUtils, TestCase):
    """
    Tests for the `wagtail.signals.page_slug_changed` signal
    """

    def setUp(self):
        # Find root page
        site = Site.objects.select_related("root_page").get(is_default_site=True)
        root_page = site.root_page

        # Create two sections
        self.section_a = SimplePage(
            title="Section A", slug="section-a", content="hello"
        )
        root_page.add_child(instance=self.section_a)

        self.section_b = SimplePage(
            title="Section B", slug="section-b", content="hello"
        )
        root_page.add_child(instance=self.section_b)

        # Add test page to section A
        self.test_page = SimplePage(
            title="Hello world! A", slug="hello-world-a", content="hello"
        )
        self.section_a.add_child(instance=self.test_page)

    def test_signal_emitted_on_slug_change(self):
        # Connect a mock signal handler to the signal
        handler = mock.MagicMock()
        page_slug_changed.connect(handler)

        old_page = SimplePage.objects.get(id=self.test_page.id)

        try:
            self.test_page.slug = "updated"
            with self.captureOnCommitCallbacks(execute=True):
                self.test_page.save()
        finally:
            # Disconnect mock handler to prevent cross-test pollution
            page_slug_changed.disconnect(handler)

        # Check the signal was fired
        self.assertEqual(handler.call_count, 1)
        handler.assert_called_with(
            signal=mock.ANY,
            sender=SimplePage,
            instance=self.test_page,
            instance_before=old_page,
        )

    def test_signal_not_emitted_on_title_change(self):
        # Connect a mock signal handler to the signal
        handler = mock.MagicMock()
        page_slug_changed.connect(handler)

        try:
            self.test_page.title = "Goodnight Moon!"
            # NOTE: Even though we're not expecting anything to happen here,
            # we need to invoke the callbacks via captureOnCommitCallbacks the same way
            # the same way we do in ``test_signal_emitted_on_slug_change``,
            # otherwise this test wouldn't prove anything.
            with self.captureOnCommitCallbacks(execute=True):
                self.test_page.save()
        finally:
            # Disconnect mock handler to prevent cross-test pollution
            page_slug_changed.disconnect(handler)

        # Check the signal was NOT fired
        self.assertEqual(handler.call_count, 0)

    def test_signal_not_emitted_on_page_move(self):
        # Connect a mock signal handler to the signal
        handler = mock.MagicMock()
        page_slug_changed.connect(handler)

        try:
            # NOTE: Even though we're not expecting anything to happen here,
            # we need to invoke the callbacks via captureOnCommitCallbacks the same way
            # the same way we do in ``test_signal_emitted_on_slug_change``,
            # otherwise this test wouldn't prove anything.
            with self.captureOnCommitCallbacks(execute=True):
                self.test_page.move(self.section_b, pos="last-child")
        finally:
            # Disconnect mock handler to prevent cross-test pollution
            page_slug_changed.disconnect(handler)

        # Check the signal was NOT fired
        self.assertEqual(handler.call_count, 0)
