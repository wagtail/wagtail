from django.test import TestCase

from wagtail.wagtailsearch import signal_handlers
from wagtail.tests.search import models


class TestGetIndexedInstance(TestCase):
    def test_gets_instance(self):
        obj = models.SearchTest(
            title="Hello",
            live=True,
        )
        obj.save()

        # Should just return the object
        indexed_instance = signal_handlers.get_indexed_instance(obj)
        self.assertEqual(indexed_instance, obj)

    def test_gets_specific_class(self):
        obj = models.SearchTestChild(
            title="Hello",
            live=True,
        )
        obj.save()

        # Running the command with the parent class should find the specific class again
        indexed_instance = signal_handlers.get_indexed_instance(obj.searchtest_ptr)
        self.assertEqual(indexed_instance, obj)

    def test_blocks_not_in_indexed_objects(self):
        obj = models.SearchTestChild(
            title="Don't index me!",
            live=True,
        )
        obj.save()

        # We've told it not to index anything with the title "Don't index me"
        # get_indexed_instance should return None
        indexed_instance = signal_handlers.get_indexed_instance(obj.searchtest_ptr)
        self.assertEqual(indexed_instance, None)
