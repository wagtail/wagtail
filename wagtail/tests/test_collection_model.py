from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from wagtail.models import Collection
from wagtail.models.media import CollectionViewRestriction


class TestCollectionTreeOperations(TestCase):
    def setUp(self):
        self.root_collection = Collection.get_first_root_node()
        self.holiday_photos_collection = self.root_collection.add_child(
            name="Holiday photos"
        )
        self.evil_plans_collection = self.root_collection.add_child(name="Evil plans")
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
            list(self.holiday_photos_collection.get_ancestors().order_by("path")),
            [self.root_collection],
        )
        self.assertEqual(
            list(
                self.holiday_photos_collection.get_ancestors(inclusive=True).order_by(
                    "path"
                )
            ),
            [self.root_collection, self.holiday_photos_collection],
        )

    def test_get_descendants(self):
        self.assertEqual(
            list(self.root_collection.get_descendants().order_by("path")),
            [self.evil_plans_collection, self.holiday_photos_collection],
        )
        self.assertEqual(
            list(self.root_collection.get_descendants(inclusive=True).order_by("path")),
            [
                self.root_collection,
                self.evil_plans_collection,
                self.holiday_photos_collection,
            ],
        )

    def test_get_siblings(self):
        self.assertEqual(
            list(self.holiday_photos_collection.get_siblings().order_by("path")),
            [self.evil_plans_collection, self.holiday_photos_collection],
        )
        self.assertEqual(
            list(
                self.holiday_photos_collection.get_siblings(inclusive=False).order_by(
                    "path"
                )
            ),
            [self.evil_plans_collection],
        )

    def test_get_next_siblings(self):
        self.assertEqual(
            list(self.evil_plans_collection.get_next_siblings().order_by("path")),
            [self.holiday_photos_collection],
        )
        self.assertEqual(
            list(
                self.holiday_photos_collection.get_next_siblings(
                    inclusive=True
                ).order_by("path")
            ),
            [self.holiday_photos_collection],
        )
        self.assertEqual(
            list(self.holiday_photos_collection.get_next_siblings().order_by("path")),
            [],
        )

    def test_get_prev_siblings(self):
        self.assertEqual(
            list(self.holiday_photos_collection.get_prev_siblings().order_by("path")),
            [self.evil_plans_collection],
        )
        self.assertEqual(
            list(self.evil_plans_collection.get_prev_siblings().order_by("path")), []
        )
        self.assertEqual(
            list(
                self.evil_plans_collection.get_prev_siblings(inclusive=True).order_by(
                    "path"
                )
            ),
            [self.evil_plans_collection],
        )


class TestCollectionViewPrivacy(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root_collection = Collection.get_first_root_node()
        cls.public_collection = cls.root_collection.add_child(name="Public_photos1")
        cls.private_collection = cls.root_collection.add_child(name="Private_photos1")
        CollectionViewRestriction.objects.create(
            collection=cls.private_collection,
            restriction_type=CollectionViewRestriction.LOGIN,
        )
        cls.root_collection.refresh_from_db()
        cls.private_collection.refresh_from_db()
        cls.public_collection.refresh_from_db()

        cls.sub_private_collection = cls.private_collection.add_child(
            name="Sub_private_photos1"
        )

        cls.sub_public_collection = cls.public_collection.add_child(
            name="Sub_public_photos1"
        )

        get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com", password="password"
        )

    def test_admin_displays_private_tag_for_private_base_collections(self):
        self.client.login(username="admin", password="password")
        request = self.client.get(
            reverse("wagtailadmin_collections:edit", args=[self.private_collection.pk])
        )

        self.assertTrue('class="privacy-indicator private"' in str(request.content))
        self.assertFalse('class="privacy-indicator "' in str(request.content))

    def test_admin_displays_private_tag_for_private_sub_collections(self):
        self.client.login(username="admin", password="password")
        request = self.client.get(
            reverse(
                "wagtailadmin_collections:edit", args=[self.sub_private_collection.pk]
            )
        )

        self.assertTrue('class="privacy-indicator private"' in str(request.content))
        self.assertFalse('class="privacy-indicator public"' in str(request.content))

    def test_admin_displays_public_tag_for_public_base_collections(self):
        self.client.login(username="admin", password="password")
        request = self.client.get(
            reverse("wagtailadmin_collections:edit", args=[self.public_collection.pk])
        )

        self.assertTrue('class="privacy-indicator public"' in str(request.content))
        self.assertFalse('class="privacy-indicator private"' in str(request.content))

    def test_admin_displays_public_tag_for_public_sub_collections(self):
        self.client.login(username="admin", password="password")
        request = self.client.get(
            reverse(
                "wagtailadmin_collections:edit", args=[self.sub_public_collection.pk]
            )
        )

        self.assertTrue('class="privacy-indicator public"' in str(request.content))
        self.assertFalse('class="privacy-indicator private"' in str(request.content))
