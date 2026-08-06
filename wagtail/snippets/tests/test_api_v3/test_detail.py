from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.test.testapp.models import Advert
from wagtail.test.utils import WagtailTestUtils


class TestV3SnippetDetail(TestV3Base, WagtailTestUtils, TestCase):
    def setUp(self):
        super().setUp()
        self.advert = Advert.objects.create(text="Advert 1", url="https://wagtail.org")

    def get_response(self, pk):
        return self.client.get(
            reverse(
                "wagtailapi_v3:detail_snippet",
                kwargs={"type": "tests.Advert", "pk": pk},
            )
        )

    def test_anonymous_returns_401(self):
        response = self.get_response(self.advert.pk)
        self.assert_problem_response(
            response,
            status_code=401,
            detail_contains="Authentication required",
        )

    def test_detail_returns_correct_fields(self):
        self.login()
        response = self.get_response(self.advert.pk)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(set(content.keys()), {"id", "url", "text", "tags", "meta"})
        self.assertEqual(content["id"], self.advert.pk)
        self.assertEqual(content["text"], "Advert 1")
        self.assertEqual(content["url"], "https://wagtail.org")
        self.assertEqual(content["meta"]["type"], "tests.Advert")

    def test_user_without_any_permission_gets_403(self):
        self.create_user(username="noperms", password="password")
        self.login(username="noperms", password="password")
        response = self.get_response(self.advert.pk)
        self.assert_problem_response(
            response,
            status_code=403,
            detail_contains="Permission denied",
        )

    def test_unknown_pk_returns_404(self):
        self.login()
        response = self.get_response(999999)
        self.assert_problem_response(
            response,
            status_code=404,
            detail_contains="No Advert matches the given query.",
        )

    @override_settings(WAGTAILAPI_BASE_URL="https://api.example.com")
    def test_detail_url_uses_base_url_setting(self):
        self.login()
        response = self.get_response(self.advert.pk)
        content = response.json()
        self.assertTrue(
            content["meta"]["detail_url"].startswith("https://api.example.com")
        )
        self.assertIn(
            f"/api/v3/snippets/tests.Advert/{self.advert.pk}/",
            content["meta"]["detail_url"],
        )
