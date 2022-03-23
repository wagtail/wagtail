from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.documents.models import Document
from wagtail.models import Collection, GroupCollectionPermission
from wagtail.test.utils import WagtailTestUtils


class CollectionInstanceTestUtils:
    def setUp(self):
        """
        Common setup for testing collection views with per-instance permissions
        """
        collection_content_type = ContentType.objects.get_for_model(Collection)
        self.add_permission = Permission.objects.get(
            content_type=collection_content_type, codename="add_collection"
        )
        self.change_permission = Permission.objects.get(
            content_type=collection_content_type, codename="change_collection"
        )
        self.delete_permission = Permission.objects.get(
            content_type=collection_content_type, codename="delete_collection"
        )
        admin_permission = Permission.objects.get(codename="access_admin")

        self.root_collection = Collection.get_first_root_node()
        self.finance_collection = self.root_collection.add_child(name="Finance")
        self.marketing_collection = self.root_collection.add_child(name="Marketing")
        self.marketing_sub_collection = self.marketing_collection.add_child(
            name="Digital Marketing"
        )
        self.marketing_sub_collection_2 = self.marketing_collection.add_child(
            name="Direct Mail Marketing"
        )

        self.marketing_group = Group.objects.create(name="Marketing Group")
        self.marketing_group.permissions.add(admin_permission)
        self.marketing_user = self.create_user("marketing", password="password")
        self.marketing_user.groups.add(self.marketing_group)


class TestCollectionsIndexViewAsSuperuser(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse("wagtailadmin_collections:index"), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/collections/index.html")

        # Initially there should be no collections listed
        # (Root should not be shown)
        self.assertContains(response, "No collections have been created.")

        root_collection = Collection.get_first_root_node()
        self.collection = root_collection.add_child(name="Holiday snaps")

        # Now the listing should contain our collection
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/collections/index.html")
        self.assertNotContains(response, "No collections have been created.")
        self.assertContains(response, "Holiday snaps")

    def test_ordering(self):
        root_collection = Collection.get_first_root_node()
        root_collection.add_child(name="Milk")
        root_collection.add_child(name="Bread")
        root_collection.add_child(name="Avocado")
        response = self.get()
        # Note that the Collections have been automatically sorted by name.
        self.assertEqual(
            [collection.name for collection in response.context["object_list"]],
            ["Avocado", "Bread", "Milk"],
        )

    def test_nested_ordering(self):
        root_collection = Collection.get_first_root_node()

        vegetables = root_collection.add_child(name="Vegetable")
        vegetables.add_child(name="Spinach")
        vegetables.add_child(name="Cucumber")

        animals = root_collection.add_child(name="Animal")
        animals.add_child(name="Dog")
        animals.add_child(name="Cat")

        response = self.get()
        # Note that while we added the collections at level 1 in reverse-alpha order, they come back out in alpha order.
        # And we added the Collections at level 2 in reverse-alpha order as well, but they were also alphabetized
        # within their respective trees. This is the result of setting Collection.node_order_by = ['name'].
        self.assertEqual(
            [collection.name for collection in response.context["object_list"]],
            ["Animal", "Cat", "Dog", "Vegetable", "Cucumber", "Spinach"],
        )


class TestCollectionsIndexView(CollectionInstanceTestUtils, TestCase, WagtailTestUtils):
    def setUp(self):
        super().setUp()
        self.login(self.marketing_user, password="password")

    def get(self, params={}):
        return self.client.get(reverse("wagtailadmin_collections:index"), params)

    def test_marketing_user_no_permissions(self):
        response = self.get()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.context["message"],
            "Sorry, you do not have permission to access this area.",
        )

    def test_marketing_user_with_change_permission(self):
        # Grant the marketing group permission to make changes to their collections
        GroupCollectionPermission.objects.create(
            group=self.marketing_group,
            collection=self.marketing_collection,
            permission=self.change_permission,
        )

        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [collection.name for collection in response.context["object_list"]],
            ["Marketing", "Digital Marketing", "Direct Mail Marketing"],
        )
        self.assertNotContains(response, "Finance")
        self.assertNotContains(response, "Add a collection")

    def test_marketing_user_with_add_permission(self):
        # Grant the marketing group permission to add to their collections
        GroupCollectionPermission.objects.create(
            group=self.marketing_group,
            collection=self.marketing_collection,
            permission=self.add_permission,
        )

        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [collection.name for collection in response.context["object_list"]],
            ["Marketing", "Digital Marketing", "Direct Mail Marketing"],
        )
        self.assertNotContains(response, "Finance")
        self.assertContains(response, "Add a collection")

    def test_marketing_user_with_delete_permission(self):
        # Grant the marketing group permission to add to their collections
        GroupCollectionPermission.objects.create(
            group=self.marketing_group,
            collection=self.marketing_collection,
            permission=self.delete_permission,
        )

        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [collection.name for collection in response.context["object_list"]],
            ["Marketing", "Digital Marketing", "Direct Mail Marketing"],
        )
        self.assertNotContains(response, "Finance")
        self.assertNotContains(response, "Add a collection")

    def test_marketing_user_with_add_permission_on_root(self):
        # Grant the marketing group permission to add to root colection
        GroupCollectionPermission.objects.create(
            group=self.marketing_group,
            collection=self.root_collection,
            permission=self.add_permission,
        )

        response = self.get()
        self.assertEqual(response.status_code, 200)
        # (Root should not be shown)
        self.assertEqual(
            [collection.name for collection in response.context["object_list"]],
            ["Finance", "Marketing", "Digital Marketing", "Direct Mail Marketing"],
        )
        self.assertContains(response, "Add a collection")


class TestAddCollectionAsSuperuser(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()
        self.root_collection = Collection.get_first_root_node()

    def get(self, params={}):
        return self.client.get(reverse("wagtailadmin_collections:add"), params)

    def post(self, post_data={}):
        return self.client.post(reverse("wagtailadmin_collections:add"), post_data)

    def test_get(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.root_collection.name)

    def test_post(self):
        response = self.post(
            {
                "name": "Holiday snaps",
                "parent": self.root_collection.id,
            }
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailadmin_collections:index"))

        # Check that the collection was created and is a child of root
        self.assertEqual(Collection.objects.filter(name="Holiday snaps").count(), 1)
        self.assertEqual(
            Collection.objects.get(name="Holiday snaps").get_parent(),
            self.root_collection,
        )


class TestAddCollection(CollectionInstanceTestUtils, TestCase, WagtailTestUtils):
    def setUp(self):
        super().setUp()
        self.login(self.marketing_user, password="password")

    def get(self, params={}):
        return self.client.get(reverse("wagtailadmin_collections:add"), params)

    def post(self, post_data={}):
        return self.client.post(reverse("wagtailadmin_collections:add"), post_data)

    def test_marketing_user_no_permissions(self):
        response = self.get()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.context["message"],
            "Sorry, you do not have permission to access this area.",
        )

    def test_marketing_user_with_add_permission(self):
        # Grant the marketing group permission to manage their collection
        GroupCollectionPermission.objects.create(
            group=self.marketing_group,
            collection=self.marketing_collection,
            permission=self.add_permission,
        )

        response = self.post(
            {
                "name": "Affiliate Marketing",
                "parent": self.marketing_collection.id,
            }
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailadmin_collections:index"))

        # Check that the collection was created and is a child of Marketing
        self.assertEqual(
            Collection.objects.filter(name="Affiliate Marketing").count(), 1
        )
        self.assertEqual(
            Collection.objects.get(name="Affiliate Marketing").get_parent(),
            self.marketing_collection,
        )

    def test_marketing_user_cannot_add_outside_their_hierarchy(self):
        # Grant the marketing group permission to manage their collection
        GroupCollectionPermission.objects.create(
            group=self.marketing_group,
            collection=self.marketing_collection,
            permission=self.add_permission,
        )

        # This user can't add to root collection
        response = self.post(
            {
                "name": "Affiliate Marketing",
                "parent": self.root_collection.id,
            }
        )
        self.assertEqual(
            response.context["form"].errors["parent"],
            ["Select a valid choice. That choice is not one of the available choices."],
        )


class TestEditCollectionAsSuperuser(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()
        self.root_collection = Collection.get_first_root_node()
        self.collection = self.root_collection.add_child(name="Holiday snaps")
        self.l1 = self.root_collection.add_child(name="Level 1")
        self.l2 = self.l1.add_child(name="Level 2")
        self.l3 = self.l2.add_child(name="Level 3")

    def get(self, params={}, collection_id=None):
        return self.client.get(
            reverse(
                "wagtailadmin_collections:edit",
                args=(collection_id or self.collection.id,),
            ),
            params,
        )

    def post(self, post_data={}, collection_id=None):
        return self.client.post(
            reverse(
                "wagtailadmin_collections:edit",
                args=(collection_id or self.collection.id,),
            ),
            post_data,
        )

    def test_get(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Delete collection")

    def test_cannot_edit_root_collection(self):
        response = self.get(collection_id=self.root_collection.id)
        self.assertEqual(response.status_code, 404)

    def test_admin_url_finder(self):
        expected_url = "/admin/collections/%d/" % self.l2.pk
        url_finder = AdminURLFinder(self.user)
        self.assertEqual(url_finder.get_edit_url(self.l2), expected_url)

    def test_get_nonexistent_collection(self):
        response = self.get(collection_id=100000)
        self.assertEqual(response.status_code, 404)

    def test_move_collection(self):
        self.post({"name": "Level 2", "parent": self.root_collection.pk}, self.l2.pk)
        self.assertEqual(
            Collection.objects.get(pk=self.l2.pk).get_parent().pk,
            self.root_collection.pk,
        )

    def test_cannot_move_parent_collection_to_descendant(self):
        response = self.post({"name": "Level 2", "parent": self.l3.pk}, self.l2.pk)
        self.assertEqual(
            response.context["message"],
            "The collection could not be saved due to errors.",
        )
        self.assertContains(response, "Please select another parent")

    def test_rename_collection(self):
        data = {"name": "Skiing photos", "parent": self.root_collection.id}
        response = self.post(data, self.collection.pk)

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailadmin_collections:index"))

        # Check that the collection was edited
        self.assertEqual(
            Collection.objects.get(id=self.collection.id).name, "Skiing photos"
        )


class TestEditCollection(CollectionInstanceTestUtils, TestCase, WagtailTestUtils):
    def setUp(self):
        super().setUp()
        # Grant the marketing group permission to edit their collection
        self.users_change_permission = GroupCollectionPermission.objects.create(
            group=self.marketing_group,
            collection=self.marketing_collection,
            permission=self.change_permission,
        )
        # Grant the marketing group permission to add collections under this collection
        self.users_add_permission = GroupCollectionPermission.objects.create(
            group=self.marketing_group,
            collection=self.marketing_collection,
            permission=self.add_permission,
        )
        self.login(self.marketing_user, password="password")

    def get(self, collection_id, params={}):
        return self.client.get(
            reverse("wagtailadmin_collections:edit", args=(collection_id,)), params
        )

    def post(self, collection_id, post_data={}):
        return self.client.post(
            reverse("wagtailadmin_collections:edit", args=(collection_id,)), post_data
        )

    def test_marketing_user_no_change_permission(self):
        self.users_change_permission.delete()
        response = self.get(collection_id=self.marketing_collection.id)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.context["message"],
            "Sorry, you do not have permission to access this area.",
        )

    def test_marketing_user_no_change_permission_post(self):
        self.users_change_permission.delete()
        response = self.post(self.marketing_collection.id, {})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.context["message"],
            "Sorry, you do not have permission to access this area.",
        )

    def test_marketing_user_can_move_collection(self):
        # Retrieve edit form and check fields
        response = self.get(collection_id=self.marketing_sub_collection.id)
        self.assertEqual(response.status_code, 200)
        form_fields = response.context["form"].fields
        self.assertEqual(type(form_fields["name"].widget).__name__, "TextInput")
        self.assertEqual(
            type(form_fields["parent"].widget).__name__, "SelectWithDisabledOptions"
        )
        # Now move the collection and check it did get moved and renamed
        self.post(
            self.marketing_sub_collection.pk,
            {
                "name": "New Collection Name",
                "parent": self.marketing_sub_collection_2.pk,
            },
        )
        self.assertEqual(
            Collection.objects.get(pk=self.marketing_sub_collection.pk).name,
            "New Collection Name",
        )
        self.assertEqual(
            Collection.objects.get(pk=self.marketing_sub_collection.pk).get_parent(),
            self.marketing_sub_collection_2,
        )

    def test_marketing_user_cannot_move_collection_if_no_add_permission(self):
        self.users_add_permission.delete()
        response = self.get(collection_id=self.marketing_sub_collection.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["form"].fields.keys()), ["name"])
        # Now try to move the collection and check it did not get moved

    def test_marketing_user_cannot_move_collection_if_no_add_permission_post(self):
        self.users_add_permission.delete()
        self.post(
            self.marketing_sub_collection.pk,
            {
                "name": "New Collection Name",
                "parent": self.marketing_sub_collection_2.pk,
            },
        )
        edited_collection = Collection.objects.get(pk=self.marketing_sub_collection.id)
        self.assertEqual(edited_collection.name, "New Collection Name")
        self.assertEqual(edited_collection.get_parent(), self.marketing_collection)

    def test_cannot_move_parent_collection_to_descendant(self):
        self.post(
            self.marketing_collection.pk,
            {
                "name": "New Collection Name",
                "parent": self.marketing_sub_collection_2.pk,
            },
        )
        self.assertEqual(
            Collection.objects.get(pk=self.marketing_collection.pk).get_parent(),
            self.root_collection,
        )

    def test_marketing_user_cannot_move_collection_permissions_are_assigned_to(self):
        response = self.get(collection_id=self.marketing_collection.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["form"].fields.keys()), ["name"])
        self.assertNotContains(response, "Delete collection")

    def test_marketing_user_cannot_move_collection_permissions_are_assigned_to_post(
        self,
    ):
        # Grant the marketing group permission to another collection so there is a valid destination
        GroupCollectionPermission.objects.create(
            group=self.marketing_group,
            collection=self.finance_collection,
            permission=self.add_permission,
        )
        # We can move nodes lower on the tree
        self.post(
            self.marketing_sub_collection.id,
            {"name": "Moved Sub", "parent": self.finance_collection.id},
        )
        self.assertEqual(
            Collection.objects.get(pk=self.marketing_sub_collection.pk).get_parent(),
            self.finance_collection,
        )

        # But we can't move the node to which our edit permission was assigned; update is ignored
        self.post(
            self.marketing_collection.id,
            {
                "name": self.marketing_collection.name,
                "parent": self.finance_collection.id,
            },
        )
        self.assertEqual(
            Collection.objects.get(pk=self.marketing_collection.pk).get_parent(),
            self.root_collection,
        )

    def test_page_shows_delete_link_only_if_delete_permitted(self):
        # Retrieve edit form and check fields
        response = self.get(collection_id=self.marketing_sub_collection.id)
        self.assertNotContains(response, "Delete collection")
        # Add delete permission to parent collection an try again
        GroupCollectionPermission.objects.create(
            group=self.marketing_group,
            collection=self.marketing_collection,
            permission=self.delete_permission,
        )
        response = self.get(collection_id=self.marketing_sub_collection.id)
        self.assertContains(response, "Delete collection")


class TestDeleteCollectionAsSuperuser(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()
        self.root_collection = Collection.get_first_root_node()
        self.collection = self.root_collection.add_child(name="Holiday snaps")

    def get(self, params={}, collection_id=None):
        return self.client.get(
            reverse(
                "wagtailadmin_collections:delete",
                args=(collection_id or self.collection.id,),
            ),
            params,
        )

    def post(self, post_data={}, collection_id=None):
        return self.client.post(
            reverse(
                "wagtailadmin_collections:delete",
                args=(collection_id or self.collection.id,),
            ),
            post_data,
        )

    def test_get(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/confirm_delete.html")

    def test_cannot_delete_root_collection(self):
        response = self.get(collection_id=self.root_collection.id)
        self.assertEqual(response.status_code, 404)

    def test_get_nonexistent_collection(self):
        response = self.get(collection_id=100000)
        self.assertEqual(response.status_code, 404)

    def test_get_nonempty_collection(self):
        Document.objects.create(title="Test document", collection=self.collection)

        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/collections/delete_not_empty.html"
        )

    def test_get_collection_with_descendent(self):
        self.collection.add_child(instance=Collection(name="Test collection"))

        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/collections/delete_not_empty.html"
        )

    def test_post(self):
        response = self.post()

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailadmin_collections:index"))

        # Check that the collection was deleted
        with self.assertRaises(Collection.DoesNotExist):
            Collection.objects.get(id=self.collection.id)

    def test_post_nonempty_collection(self):
        Document.objects.create(title="Test document", collection=self.collection)

        response = self.post()
        self.assertEqual(response.status_code, 403)

        # Check that the collection was not deleted
        self.assertTrue(Collection.objects.get(id=self.collection.id))

    def test_post_collection_with_descendant(self):
        self.collection.add_child(instance=Collection(name="Test collection"))

        response = self.post()
        self.assertEqual(response.status_code, 403)

        # Check that the collection was not deleted
        self.assertTrue(Collection.objects.get(id=self.collection.id))

    def test_post_root_collection(self):
        # first we have to clear out the root collection so it is empty
        self.collection.delete()

        response = self.post(collection_id=self.root_collection.id)
        self.assertEqual(response.status_code, 404)
        # Check that the collection was not deleted
        self.assertTrue(Collection.objects.get(id=self.root_collection.id))


class TestDeleteCollection(CollectionInstanceTestUtils, TestCase, WagtailTestUtils):
    def setUp(self):
        super().setUp()
        # Grant the marketing group permission to delete
        self.users_delete_permission = GroupCollectionPermission.objects.create(
            group=self.marketing_group,
            collection=self.marketing_collection,
            permission=self.delete_permission,
        )
        self.login(self.marketing_user, password="password")

    def get(self, collection_id, params={}):
        return self.client.get(
            reverse("wagtailadmin_collections:delete", args=(collection_id,)), params
        )

    def post(self, collection_id, post_data={}):
        return self.client.post(
            reverse("wagtailadmin_collections:delete", args=(collection_id,)), post_data
        )

    def test_get(self):
        response = self.get(collection_id=self.marketing_sub_collection.id)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/confirm_delete.html")

    def test_post(self):
        response = self.post(collection_id=self.marketing_sub_collection.id)
        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailadmin_collections:index"))

        # Check that the collection was deleted
        with self.assertRaises(Collection.DoesNotExist):
            Collection.objects.get(id=self.marketing_sub_collection.id)

    def test_cannot_delete_someone_elses_collection(self):
        response = self.get(self.finance_collection.id)
        self.assertEqual(response.status_code, 404)

    def test_cannot_delete_someone_elses_collection_post(self):
        response = self.post(self.finance_collection.id)
        self.assertEqual(response.status_code, 404)
        # Check that the collection was not deleted
        self.assertTrue(Collection.objects.get(id=self.marketing_sub_collection.id))

    def test_cannot_delete_their_own_root_collection(self):
        response = self.get(self.marketing_collection.id)
        self.assertEqual(response.status_code, 404)

    def test_cannot_delete_their_own_root_collection_post(self):
        response = self.post(self.marketing_collection.id)
        self.assertEqual(response.status_code, 404)
        # Check that the collection was not deleted
        self.assertTrue(Collection.objects.get(id=self.marketing_collection.id))

    def test_cannot_delete_collection_with_descendants(self):
        self.marketing_sub_collection.add_child(
            instance=Collection(name="Another collection")
        )

        response = self.get(self.marketing_sub_collection.id)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/collections/delete_not_empty.html"
        )

    def test_cannot_delete_collection_with_descendants_post(self):
        self.marketing_sub_collection.add_child(
            instance=Collection(name="Another collection")
        )

        response = self.post(self.marketing_sub_collection.id)
        self.assertEqual(response.status_code, 403)

        # Check that the collection was not deleted
        self.assertTrue(Collection.objects.get(id=self.marketing_sub_collection.id))
