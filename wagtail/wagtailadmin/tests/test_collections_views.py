from __future__ import unicode_literals
from django.test import TestCase
from django.core.urlresolvers import reverse

from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailcore.models import Collection


class TestCollectionsIndexView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_collections:index'), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/collections/index.html')


class TestAddCollection(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_collections:add'), params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailadmin_collections:add'), post_data)

    def test_get(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.post({
            'name': "Holiday snaps",
        })

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailadmin_collections:index'))

        # Check that the collection was created and is a child of root
        self.assertEqual(Collection.objects.filter(name="Holiday snaps").count(), 1)

        root_collection = Collection.get_first_root_node()
        self.assertEqual(
            Collection.objects.get(name="Holiday snaps").get_parent(),
            root_collection
        )


class TestEditCollection(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()
        root_collection = Collection.get_first_root_node()
        self.collection = root_collection.add_child(name="Holiday snaps")

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

    def test_get_nonexistent_collection(self):
        response = self.get(collection_id=100000)
        self.assertEqual(response.status_code, 404)

    def test_post(self):
        response = self.post({
            'name': "Skiing photos",
        })

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailadmin_collections:index'))

        # Check that the collection was edited
        self.assertEqual(
            Collection.objects.get(id=self.collection.id).name,
            "Skiing photos"
        )


class TestDeleteCollection(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()
        root_collection = Collection.get_first_root_node()
        self.collection = root_collection.add_child(name="Holiday snaps")

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

    def test_get_nonexistent_collection(self):
        response = self.get(collection_id=100000)
        self.assertEqual(response.status_code, 404)

    def test_post(self):
        response = self.post()

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailadmin_collections:index'))

        # Check that the collection was deleted
        with self.assertRaises(Collection.DoesNotExist):
            Collection.objects.get(id=self.collection.id)
