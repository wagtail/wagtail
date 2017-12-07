from django.test import TestCase
from django.urls import reverse

from wagtail.tests.utils import WagtailTestUtils
from wagtail.core.models import Collection
from wagtail.documents.models import Document


class TestCollectionsIndexView(TestCase, WagtailTestUtils):
    # TODO: Need to test index view for other collections besides root
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_collections:index'), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/collections/index.html')

        # Initially there should be no collections listed
        # (Root should not be shown)
        self.assertContains(response, "No collections have been created.")

        root_collection = Collection.get_first_root_node()
        self.collection = root_collection.add_child(name="Holiday snaps")

        # Now the listing should contain our collection
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/collections/index.html')
        self.assertNotContains(response, "No collections have been created.")
        self.assertContains(response, "Holiday snaps")


class TestAddCollection(TestCase, WagtailTestUtils):
    # TODO: Check that the collection gets added to the correct parent besides Root
    def setUp(self):
        self.login()
        self.root_collection = Collection.get_first_root_node()

    def get(self, parent_id, params={}):
        return self.client.get(reverse('wagtailadmin_collections:add_child', args=(parent_id, )), params)

    def post(self, parent_id, post_data={}):
        return self.client.post(reverse('wagtailadmin_collections:add_child', args=(parent_id, )), post_data)

    def test_get(self):
        response = self.get(self.root_collection.pk)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.post(self.root_collection.pk, {
            'name': "Holiday snaps",
        })

        # Should redirect back to index
        self.assertRedirects(response, reverse(
            'wagtailadmin_collections:parent_index', args=(self.root_collection.pk, )
        ))

        # Check that the collection was created and is a child of root
        self.assertEqual(Collection.objects.filter(name="Holiday snaps").count(), 1)

        self.assertEqual(
            Collection.objects.get(name="Holiday snaps").get_parent(),
            self.root_collection
        )


class TestEditCollection(TestCase, WagtailTestUtils):
    # TODO: Add tests for editing collections that are children of collections other than Root
    def setUp(self):
        self.login()
        self.root_collection = Collection.get_first_root_node()
        self.collection = self.root_collection.add_child(name="Holiday snaps")

    def get(self, params={}, collection_id=None):
        return self.client.get(
            reverse('wagtailadmin_collections:edit', args=(collection_id or self.collection.id,)),
            params
        )

    def post(self, post_data={}, collection_id=None):
        return self.client.post(
            reverse('wagtailadmin_collections:edit', args=(collection_id or self.collection.id,)),
            post_data
        )

    def test_get(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)

    def test_cannot_edit_root_collection(self):
        response = self.get(collection_id=self.root_collection.id)
        self.assertEqual(response.status_code, 403)

    def test_get_nonexistent_collection(self):
        response = self.get(collection_id=100000)
        self.assertEqual(response.status_code, 404)

    def test_post(self):
        response = self.post({
            'name': "Skiing photos",
        })

        # Should redirect back to index
        self.assertRedirects(response, reverse(
            'wagtailadmin_collections:parent_index', args=(self.root_collection.pk, )
        ))

        # Check that the collection was edited
        self.assertEqual(
            Collection.objects.get(id=self.collection.id).name,
            "Skiing photos"
        )


class TestDeleteCollection(TestCase, WagtailTestUtils):
    # TODO: Test for collection inheritance changes
    def setUp(self):
        self.login()
        self.root_collection = Collection.get_first_root_node()
        self.collection = self.root_collection.add_child(name="Holiday snaps")

    def get(self, params={}, collection_id=None):
        return self.client.get(
            reverse('wagtailadmin_collections:delete', args=(collection_id or self.collection.id,)),
            params
        )

    def post(self, post_data={}, collection_id=None):
        return self.client.post(
            reverse('wagtailadmin_collections:delete', args=(collection_id or self.collection.id,)),
            post_data
        )

    def test_get(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/generic/confirm_delete.html')

    def test_cannot_delete_root_collection(self):
        response = self.get(collection_id=self.root_collection.id)
        self.assertEqual(response.status_code, 403)

    def test_get_nonexistent_collection(self):
        response = self.get(collection_id=100000)
        self.assertEqual(response.status_code, 404)

    def test_get_nonempty_collection(self):
        Document.objects.create(
            title="Test document", collection=self.collection
        )

        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/collections/delete_not_empty.html')

    def test_post(self):
        response = self.post()

        # Should redirect back to index
        self.assertRedirects(response, reverse(
            'wagtailadmin_collections:parent_index', args=(self.root_collection.pk, )
        ))

        # Check that the collection was deleted
        with self.assertRaises(Collection.DoesNotExist):
            Collection.objects.get(id=self.collection.id)

    def test_post_nonempty_collection(self):
        Document.objects.create(
            title="Test document", collection=self.collection
        )

        response = self.post()
        self.assertEqual(response.status_code, 403)

        # Check that the collection was not deleted
        self.assertTrue(Collection.objects.get(id=self.collection.id))
