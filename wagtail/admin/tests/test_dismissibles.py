from django.test import TestCase
from django.urls import reverse

from wagtail.test.utils import WagtailTestUtils
from wagtail.users.models import UserProfile


class TestDismissiblesView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()
        self.profile = UserProfile.get_for_user(self.user)
        self.url = reverse("wagtailadmin_dismissibles")

    def test_get_initial(self):
        response = self.client.get(self.url)
        self.profile.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})
        self.assertEqual(self.user.wagtail_userprofile.dismissibles, {})

    def test_patch_valid(self):
        response = self.client.patch(
            self.url, data={"foo": "bar"}, content_type="application/json"
        )
        self.profile.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"foo": "bar"})
        self.assertEqual(self.user.wagtail_userprofile.dismissibles, {"foo": "bar"})

    def test_patch_invalid(self):
        response = self.client.patch(
            self.url, data="invalid", content_type="application/json"
        )
        self.profile.refresh_from_db()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.user.wagtail_userprofile.dismissibles, {})

    def test_post(self):
        # The view only accepts GET and PATCH
        response = self.client.post(self.url, data={"foo": "bar"})
        self.profile.refresh_from_db()
        self.assertEqual(response.status_code, 405)
        self.assertEqual(self.user.wagtail_userprofile.dismissibles, {})

    def test_get_without_userprofile(self):
        # GET should work even if the user doesn't have a UserProfile,
        # but it shouldn't create one
        self.profile.delete()
        response = self.client.get(self.url)
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})
        self.assertIsNone(getattr(self.user, "wagtail_userprofile", None))

    def test_patch_without_userprofile(self):
        # PATCH should work even if the user doesn't have a UserProfile,
        # in which case it should create one
        self.profile.delete()
        response = self.client.patch(
            self.url, data={"foo": "bar"}, content_type="application/json"
        )
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"foo": "bar"})
        self.assertEqual(self.user.wagtail_userprofile.dismissibles, {"foo": "bar"})
