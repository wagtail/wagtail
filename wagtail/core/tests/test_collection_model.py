from django.test import TestCase

from wagtail.core.models import Collection


class TestCollectionTreeOperations(TestCase):
    def setUp(self):
        self.root_collection = Collection.get_first_root_node()
        self.holiday_photos_collection = self.root_collection.add_child(
            name="Holiday photos"
        )
        self.evil_plans_collection = self.root_collection.add_child(
            name="Evil plans"
        )
        # self.holiday_photos_collection's path has been updated out from under it by the addition of a sibling with
        # an alphabetically earlier name (due to Collection.node_order_by = ['name']), so we need to refresh it from
        # the DB to get the new path.
        self.holiday_photos_collection.refresh_from_db()

    def test_alphabetic_sorting(self):
        old_evil_path = self.evil_plans_collection.path
        old_holiday_path = self.holiday_photos_collection.path
        # Add a child to Root that has an earlier name than "Evil plans" and "Holiday Photos".
        alpha_collection = self.root_collection.add_child(name="Alpha")
        # Take note that self.evil_plans_collection and self.holiday_photos_collection have not yet changed.
        self.assertEqual(old_evil_path, self.evil_plans_collection.path)
        self.assertEqual(old_holiday_path, self.holiday_photos_collection.path)
        # Update the two Collections from the database.
        self.evil_plans_collection.refresh_from_db()
        self.holiday_photos_collection.refresh_from_db()
        # Confirm that the "Evil plans" and "Holiday photos" paths have changed in the DB due to adding "Alpha".
        self.assertNotEqual(old_evil_path, self.evil_plans_collection.path)
        self.assertNotEqual(old_holiday_path, self.holiday_photos_collection.path)
        # Confirm that Alpha is before Evil Plans and Holiday Photos, due to Collection.node_order_by = ['name'].
        self.assertLess(alpha_collection.path, self.evil_plans_collection.path)
        self.assertLess(alpha_collection.path, self.holiday_photos_collection.path)

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
            [self.evil_plans_collection, self.holiday_photos_collection]
        )
        self.assertEqual(
            list(self.root_collection.get_descendants(inclusive=True).order_by('path')),
            [
                self.root_collection,
                self.evil_plans_collection,
                self.holiday_photos_collection
            ]
        )

    def test_get_siblings(self):
        self.assertEqual(
            list(self.holiday_photos_collection.get_siblings().order_by('path')),
            [self.evil_plans_collection, self.holiday_photos_collection]
        )
        self.assertEqual(
            list(self.holiday_photos_collection.get_siblings(inclusive=False).order_by('path')),
            [self.evil_plans_collection]
        )

    def test_get_next_siblings(self):
        self.assertEqual(
            list(
                self.evil_plans_collection.get_next_siblings().order_by('path')
            ),
            [self.holiday_photos_collection]
        )
        self.assertEqual(
            list(
                self.holiday_photos_collection.get_next_siblings(inclusive=True).order_by('path')
            ),
            [self.holiday_photos_collection]
        )
        self.assertEqual(
            list(
                self.holiday_photos_collection.get_next_siblings().order_by('path')
            ),
            []
        )

    def test_get_prev_siblings(self):
        self.assertEqual(
            list(
                self.holiday_photos_collection.get_prev_siblings().order_by('path')
            ),
            [self.evil_plans_collection]
        )
        self.assertEqual(
            list(
                self.evil_plans_collection.get_prev_siblings().order_by('path')
            ),
            []
        )
        self.assertEqual(
            list(
                self.evil_plans_collection.get_prev_siblings(inclusive=True).order_by('path')
            ),
            [self.evil_plans_collection]
        )
