import json

from django.contrib.auth.models import Group, Permission
from django.urls import reverse

from wagtail.images import get_image_model
from wagtail.models import GroupCollectionPermission

from .base import TestV3ImagesBase

Image = get_image_model()


class TestV3ImageUpdate(TestV3ImagesBase):
    def setUp(self):
        super().setUp()
        self.image = self.create_image(title="Original")

    def patch(self, image_id, data):
        return self.client.patch(
            reverse("wagtailapi_v3:update_image", kwargs={"image_id": image_id}),
            data=json.dumps(data),
            content_type="application/json",
        )

    def test_anonymous_returns_401(self):
        self.client.logout()
        response = self.patch(self.image.id, {"title": "Changed"})
        self.assert_problem_response(response, status_code=401)

    def test_superuser_can_update_title(self):
        self.login()
        response = self.patch(self.image.id, {"title": "Changed"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "Changed")
        self.image.refresh_from_db()
        self.assertEqual(self.image.title, "Changed")

    def test_partial_update_leaves_other_fields_untouched(self):
        self.login()
        self.image.description = "Keep me"
        self.image.save(update_fields=["description"])
        response = self.patch(self.image.id, {"title": "Changed"})
        self.assertEqual(response.status_code, 200)
        self.image.refresh_from_db()
        self.assertEqual(self.image.description, "Keep me")

    def test_update_focal_point(self):
        self.login()
        response = self.patch(
            self.image.id,
            {"focal_point_x": 100, "focal_point_y": 200},
        )
        self.assertEqual(response.status_code, 200)
        self.image.refresh_from_db()
        self.assertEqual(self.image.focal_point_x, 100)
        self.assertEqual(self.image.focal_point_y, 200)

    def test_update_collection_to_permitted_collection(self):
        user = self.create_user(username="editor", password="password")
        # Not "editors": MySQL's case-insensitive collation makes that
        # collide with Wagtail's default "Editors" group (0002_initial_data).
        group = Group.objects.create(name="image editors")
        user.groups.add(group)
        change_permission = Permission.objects.get(
            content_type__app_label="wagtailimages", codename="change_image"
        )
        add_permission = Permission.objects.get(
            content_type__app_label="wagtailimages", codename="add_image"
        )
        old_collection = self.image.collection
        new_collection = self.create_collection("New home")
        GroupCollectionPermission.objects.create(
            group=group, collection=old_collection, permission=change_permission
        )
        GroupCollectionPermission.objects.create(
            group=group, collection=new_collection, permission=add_permission
        )
        self.login(user)
        response = self.patch(self.image.id, {"collection_id": new_collection.id})
        self.assertEqual(response.status_code, 200)
        self.image.refresh_from_db()
        self.assertEqual(self.image.collection_id, new_collection.id)

    def test_update_to_forbidden_collection_returns_422(self):
        user = self.create_user(username="editor", password="password")
        # Distinct name from the other collection test's group (and from
        # Wagtail's default "Editors" group, which MySQL's case-insensitive
        # collation would otherwise collide with).
        group = Group.objects.create(name="collection editors")
        user.groups.add(group)
        change_permission = Permission.objects.get(
            content_type__app_label="wagtailimages", codename="change_image"
        )
        add_permission = Permission.objects.get(
            content_type__app_label="wagtailimages", codename="add_image"
        )
        GroupCollectionPermission.objects.create(
            group=group, collection=self.image.collection, permission=change_permission
        )
        # The collection field only shows when the user has more than one
        # permitted collection, so grant add on two and submit a third.
        allowed = self.create_collection("Allowed")
        also_allowed = self.create_collection("Also allowed")
        forbidden = self.create_collection("Forbidden")
        GroupCollectionPermission.objects.create(
            group=group, collection=allowed, permission=add_permission
        )
        GroupCollectionPermission.objects.create(
            group=group, collection=also_allowed, permission=add_permission
        )
        self.login(user)
        response = self.patch(self.image.id, {"collection_id": forbidden.id})
        self.assert_problem_response(
            response, status_code=422, errors=[{"loc": ["collection"]}]
        )

    def test_uploader_with_add_permission_can_edit_own_image(self):
        user = self.create_user(username="uploader", password="password")
        group = Group.objects.create(name="uploaders")
        user.groups.add(group)
        add_permission = Permission.objects.get(
            content_type__app_label="wagtailimages", codename="add_image"
        )
        GroupCollectionPermission.objects.create(
            group=group, collection=self.image.collection, permission=add_permission
        )
        self.image.uploaded_by_user = user
        self.image.save(update_fields=["uploaded_by_user"])
        self.login(user)
        response = self.patch(self.image.id, {"title": "Mine now"})
        self.assertEqual(response.status_code, 200)

    def test_cannot_edit_other_users_image_without_change_permission(self):
        owner = self.create_user(username="owner", password="password")
        user = self.create_user(username="other", password="password")
        group = Group.objects.create(name="others")
        user.groups.add(group)
        add_permission = Permission.objects.get(
            content_type__app_label="wagtailimages", codename="add_image"
        )
        GroupCollectionPermission.objects.create(
            group=group, collection=self.image.collection, permission=add_permission
        )
        self.image.uploaded_by_user = owner
        self.image.save(update_fields=["uploaded_by_user"])
        self.login(user)
        response = self.patch(self.image.id, {"title": "Theirs"})
        self.assert_problem_response(
            response,
            status_code=403,
            detail_contains=(
                "You do not have permission to perform the 'edit' "
                "action on this object."
            ),
        )

    def test_audit_log(self):
        self.login()
        self.patch(self.image.id, {"title": "Logged"})
        self.assert_log_actions(self.image, ["wagtail.edit"])
