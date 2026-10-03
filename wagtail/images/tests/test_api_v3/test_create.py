from django.contrib.auth.models import Group, Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from wagtail.images import get_image_model
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import GroupCollectionPermission

from .base import TestV3ImagesBase

Image = get_image_model()


class TestV3ImageCreate(TestV3ImagesBase):
    def post_image(self, **kwargs):
        data = {
            "file": SimpleUploadedFile(
                "test.png", get_test_image_file().file.getvalue()
            ),
        }
        data.update(kwargs)
        return self.client.post(reverse("wagtailapi_v3:create_image"), data)

    def grant_collection_permission(self, user, collection, codename="add_image"):
        # get_username() rather than .username: the test suite also runs with
        # the emailuser custom user model (no username attribute).
        group = Group.objects.create(
            name=f"group-{user.get_username()}-{collection.pk}"
        )
        user.groups.add(group)
        permission = Permission.objects.get(
            content_type__app_label="wagtailimages", codename=codename
        )
        GroupCollectionPermission.objects.create(
            group=group, collection=collection, permission=permission
        )

    def test_anonymous_returns_401(self):
        self.client.logout()
        response = self.post_image(title="Test")
        self.assert_problem_response(response, status_code=401)

    def test_superuser_can_create(self):
        self.user = self.login()
        response = self.post_image(title="New image")
        self.assertEqual(response.status_code, 201)
        content = response.json()
        self.assertEqual(content["title"], "New image")
        self.assertEqual(content["width"], 640)
        self.assertEqual(content["height"], 480)
        image = Image.objects.get(id=content["id"])
        self.assertEqual(image.uploaded_by_user, self.user)
        self.assertIsNotNone(image.file_size)
        self.assertNotEqual(image.file_hash, "")

    def test_missing_title_returns_422(self):
        self.login()
        response = self.post_image()
        self.assert_problem_response(response, status_code=422)

    def test_missing_file_returns_422(self):
        self.login()
        response = self.client.post(
            reverse("wagtailapi_v3:create_image"), {"title": "No file"}
        )
        self.assert_problem_response(response, status_code=422)

    def test_user_without_add_permission_gets_403(self):
        user = self.create_user(username="noperms", password="password")
        self.login(user)
        response = self.post_image(title="Test")
        self.assert_problem_response(
            response, status_code=403, detail_contains="Permission denied"
        )

    def test_user_with_add_permission_in_one_collection_gets_default_collection(self):
        user = self.create_user(username="adder", password="password")
        collection = self.create_collection("Only")
        self.grant_collection_permission(user, collection)
        self.login(user)
        response = self.post_image(title="Test")
        self.assertEqual(response.status_code, 201)
        image = Image.objects.get(id=response.json()["id"])
        self.assertEqual(image.collection_id, collection.id)

    def test_forbidden_collection_returns_422(self):
        user = self.create_user(username="adder", password="password")
        allowed = self.create_collection("Allowed")
        also_allowed = self.create_collection("Also allowed")
        forbidden = self.create_collection("Forbidden")
        # The form only shows the collection field when the user has more than
        # one permitted collection, so grant add on two and submit a third.
        self.grant_collection_permission(user, allowed)
        self.grant_collection_permission(user, also_allowed)
        self.login(user)
        response = self.post_image(title="Test", collection_id=forbidden.id)
        self.assert_problem_response(
            response,
            status_code=422,
            errors=[{"loc": ["collection"]}],
        )

    def test_missing_collection_with_multiple_permitted_collections_returns_422(self):
        user = self.create_user(username="adder", password="password")
        first = self.create_collection("First")
        second = self.create_collection("Second")
        self.grant_collection_permission(user, first)
        self.grant_collection_permission(user, second)
        self.login(user)
        response = self.post_image(title="Test")
        self.assert_problem_response(
            response,
            status_code=422,
            errors=[{"loc": ["collection"]}],
        )

    @override_settings(WAGTAILIMAGES_MAX_UPLOAD_SIZE=10)
    def test_oversized_file_returns_422(self):
        self.login()
        response = self.post_image(title="Test")
        self.assert_problem_response(
            response, status_code=422, errors=[{"loc": ["file"]}]
        )

    @override_settings(WAGTAILIMAGES_MAX_IMAGE_PIXELS=1000)
    def test_too_many_pixels_returns_422(self):
        self.login()
        response = self.post_image(title="Test")
        self.assert_problem_response(
            response, status_code=422, errors=[{"loc": ["file"]}]
        )

    def test_bad_extension_returns_422(self):
        self.login()
        response = self.client.post(
            reverse("wagtailapi_v3:create_image"),
            {
                "file": SimpleUploadedFile("not-an-image.txt", b"hello"),
                "title": "Test",
            },
        )
        self.assert_problem_response(
            response, status_code=422, errors=[{"loc": ["file"]}]
        )

    def test_corrupt_file_returns_422(self):
        self.login()
        response = self.client.post(
            reverse("wagtailapi_v3:create_image"),
            {
                "file": SimpleUploadedFile("bad.png", b"not really a png"),
                "title": "Test",
            },
        )
        self.assert_problem_response(
            response, status_code=422, errors=[{"loc": ["file"]}]
        )

    def test_audit_log(self):
        self.user = self.login()
        response = self.post_image(title="Logged")
        image = Image.objects.get(id=response.json()["id"])
        self.assert_log_actions(image, ["wagtail.create"])
