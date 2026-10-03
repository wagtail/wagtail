from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.test.utils import WagtailTestUtils


class TestWhoAmI(TestV3Base, WagtailTestUtils, TestCase):
    url = reverse("wagtailapi_v3:whoami")

    def test_anonymous_401(self):
        self.assert_problem_response(self.client.get(self.url), status_code=401)

    def test_superuser(self):
        user = self.create_test_user()
        self.authorize(user)
        content = self.client.get(self.url).json()
        self.assertEqual(content["user"]["username"], user.get_username())
        self.assertTrue(content["user"]["is_superuser"])
        self.assertEqual(content["groups"], [])

    def test_editor_role(self):
        group = Group.objects.create(name="API editors")
        user = WagtailTestUtils.create_user("editor")
        user.groups.add(group)
        self.authorize(user)
        content = self.client.get(self.url).json()
        self.assertEqual(content["user"]["username"], user.get_username())
        self.assertFalse(content["user"]["is_superuser"])
        self.assertEqual(content["groups"], ["API editors"])
        self.assertIn("avatar_url", content["profile"])

    def test_revoked_token_401(self):
        user = self.create_test_user()
        token = self.authorize(user)
        token.revoke()
        self.assert_problem_response(self.client.get(self.url), status_code=401)
