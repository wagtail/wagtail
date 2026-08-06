from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.test.testapp.models import Advert
from wagtail.test.utils import WagtailTestUtils


class TestV3SnippetListingBase(TestV3Base, WagtailTestUtils, TestCase):
    model = Advert

    def setUp(self):
        super().setUp()
        self.user = self.login()

    def get_response(self, **params):
        return self.client.get(
            reverse(
                "wagtailapi_v3:list_snippets",
                kwargs={"type": self.model._meta.label},
            ),
            params,
        )


class TestV3SnippetListing(TestV3SnippetListingBase):
    def setUp(self):
        super().setUp()
        Advert.objects.create(text="Advert 1")
        Advert.objects.create(text="Advert 2")

    def test_anonymous_returns_401(self):
        self.client.logout()
        response = self.get_response()
        self.assert_problem_response(
            response,
            status_code=401,
            detail_contains="Authentication required",
        )

    def test_authenticated_returns_200(self):
        response = self.get_response()
        self.assertEqual(response.status_code, 200)

    def test_response_fields(self):
        content = self.get_response().json()
        self.assertIn("count", content)
        self.assertIn("items", content)
        for item in content["items"]:
            self.assertEqual(set(item.keys()), {"id", "url", "text", "tags", "meta"})

    def test_count_matches_database(self):
        content = self.get_response().json()
        self.assertEqual(content["count"], Advert.objects.count())

    def test_user_with_any_permission_can_list(self):
        user = self.create_user(username="viewer", password="password")
        user.user_permissions.add(Permission.objects.get(codename="view_advert"))
        self.login(username="viewer", password="password")
        response = self.get_response()
        self.assertEqual(response.status_code, 200)

    def test_user_without_any_permission_gets_403(self):
        self.create_user(username="noperms", password="password")
        self.login(username="noperms", password="password")
        response = self.get_response()
        self.assert_problem_response(
            response,
            status_code=403,
            detail_contains="Permission denied",
        )

    def test_unknown_type_returns_422(self):
        response = self.client.get(
            reverse("wagtailapi_v3:list_snippets", kwargs={"type": "tests.NotASnippet"})
        )
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[{"type": "literal_error", "loc": ["path", "type"]}],
        )


class TestV3SnippetListingPagination(TestV3SnippetListingBase):
    def setUp(self):
        super().setUp()
        self.adverts = [Advert.objects.create(text=f"Advert {i}") for i in range(25)]

    def get_id_list(self, content):
        return [item["id"] for item in content["items"]]

    def test_default_limit_is_20(self):
        content = self.get_response().json()
        self.assertEqual(len(content["items"]), 20)
        self.assertEqual(content["count"], 25)

    def test_offset_and_limit_return_expected_slice(self):
        all_ids = [advert.pk for advert in self.adverts]
        content = self.get_response(offset=3, limit=2).json()
        self.assertEqual(self.get_id_list(content), all_ids[3:5])

    def test_offset_beyond_count_returns_empty_items(self):
        content = self.get_response(offset=100).json()
        self.assertEqual(content["count"], 25)
        self.assertEqual(content["items"], [])

    @override_settings(WAGTAILAPI_LIMIT_MAX=5)
    def test_limit_max_enforced(self):
        response = self.get_response(limit=10)
        self.assert_problem_response(response, status_code=400)

    @override_settings(WAGTAILAPI_LIMIT_MAX=5)
    def test_limit_within_max(self):
        content = self.get_response(limit=5).json()
        self.assertLessEqual(len(content["items"]), 5)
