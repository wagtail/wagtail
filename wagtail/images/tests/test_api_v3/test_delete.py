from django.contrib.auth.models import Group, Permission
from django.urls import reverse

from wagtail.images import get_image_model
from wagtail.models import GroupCollectionPermission

from .base import TestV3ImagesBase

Image = get_image_model()


class TestV3ImageDelete(TestV3ImagesBase):
    def delete(self, image_id):
        return self.client.delete(
            reverse("wagtailapi_v3:delete_image", kwargs={"image_id": image_id})
        )

    def test_anonymous_returns_401(self):
        image = self.create_image()
        self.client.logout()
        response = self.delete(image.id)
        self.assert_problem_response(response, status_code=401)

    def test_superuser_can_delete(self):
        self.login()
        image = self.create_image(title="Doomed")
        response = self.delete(image.id)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Image.objects.filter(id=image.id).exists())

    def test_user_without_delete_permission_gets_403(self):
        image = self.create_image()
        user = self.create_user(username="noperms", password="password")
        group = Group.objects.create(name="noperms")
        user.groups.add(group)
        add_permission = Permission.objects.get(
            content_type__app_label="wagtailimages", codename="add_image"
        )
        GroupCollectionPermission.objects.create(
            group=group, collection=image.collection, permission=add_permission
        )
        # Add-only permission is not enough to delete someone else's image
        # (the image is not owned by this user).
        self.login(user)
        response = self.delete(image.id)
        self.assert_problem_response(
            response,
            status_code=403,
            detail_contains=(
                "You do not have permission to perform the 'delete' "
                "action on this object."
            ),
        )

    def test_uploader_with_add_permission_can_delete_own_image(self):
        user = self.create_user(username="uploader", password="password")
        group = Group.objects.create(name="uploaders")
        user.groups.add(group)
        add_permission = Permission.objects.get(
            content_type__app_label="wagtailimages", codename="add_image"
        )
        image = self.create_image(uploaded_by_user=user)
        GroupCollectionPermission.objects.create(
            group=group, collection=image.collection, permission=add_permission
        )
        self.login(user)
        response = self.delete(image.id)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Image.objects.filter(id=image.id).exists())

    def test_unknown_id_returns_404(self):
        self.login()
        response = self.delete(999999)
        self.assertEqual(response.status_code, 404)

    def test_audit_log(self):
        self.login()
        image = self.create_image(title="Logged")
        self.delete(image.id)
        self.assert_log_actions(image, ["wagtail.delete"])
