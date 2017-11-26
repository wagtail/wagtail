from django.test import TestCase

from wagtail.wagtailcore.models import Collection


class TestCollectionTreeOperations(TestCase):
    def setUp(self):
        self.root_collection = Collection.get_first_root_node()
        self.holiday_photos_collection = self.root_collection.add_child(
            name="Holiday photos"
        )
        self.evil_plans_collection = self.root_collection.add_child(
            name="Evil plans"
        )

    def test_get_ancestors(self):
        self.assertEqual(
            list(self.holiday_photos_collection.get_ancestors().order_by('path')),
            [self.root_collection]
        )
        self.assertEqual(
            list(self.holiday_photos_collection.get_ancestors(inclusive=True).order_by('path')),
            [self.root_collection, self.holiday_photos_collection]
        )

    def test_get_descendants(self):
        self.assertEqual(
            list(self.root_collection.get_descendants().order_by('path')),
            [self.holiday_photos_collection, self.evil_plans_collection]
        )
        self.assertEqual(
            list(self.root_collection.get_descendants(inclusive=True).order_by('path')),
            [
                self.root_collection,
                self.holiday_photos_collection,
                self.evil_plans_collection
            ]
        )

    def test_get_siblings(self):
        self.assertEqual(
            list(self.holiday_photos_collection.get_siblings().order_by('path')),
            [self.holiday_photos_collection, self.evil_plans_collection]
        )
        self.assertEqual(
            list(self.holiday_photos_collection.get_siblings(inclusive=False).order_by('path')),
            [self.evil_plans_collection]
        )

    def test_get_next_siblings(self):
        self.assertEqual(
            list(
                self.holiday_photos_collection.get_next_siblings().order_by('path')
            ),
            [self.evil_plans_collection]
        )
        self.assertEqual(
            list(
                self.holiday_photos_collection.get_next_siblings(inclusive=True).order_by('path')
            ),
            [self.holiday_photos_collection, self.evil_plans_collection]
        )
        self.assertEqual(
            list(
                self.evil_plans_collection.get_next_siblings().order_by('path')
            ),
            []
        )

    def test_get_prev_siblings(self):
        self.assertEqual(
            list(
                self.holiday_photos_collection.get_prev_siblings().order_by('path')
            ),
            []
        )
        self.assertEqual(
            list(
                self.evil_plans_collection.get_prev_siblings().order_by('path')
            ),
            [self.holiday_photos_collection]
        )
        self.assertEqual(
            list(
                self.evil_plans_collection.get_prev_siblings(inclusive=True).order_by('path')
            ),
            [self.holiday_photos_collection, self.evil_plans_collection]
        )
