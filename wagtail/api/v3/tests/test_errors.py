import json

from django.test import TestCase
from django.urls import reverse

from wagtail.api.v3.tests.base import assert_problem_response


class TestV3ErrorResponses(TestCase):
    def test_not_found_is_problem_json(self):
        response = self.client.get(
            reverse("wagtailapi_v3:detail_page", kwargs={"page_id": 999999})
        )
        assert_problem_response(self, response, status_code=404)

    def test_validation_error_is_problem_json(self):
        response = self.client.get(
            reverse("wagtailapi_v3:list_pages"),
            {"limit": "not-a-number"},
        )
        assert_problem_response(self, response, status_code=422)
        content = json.loads(response.content.decode("UTF-8"))
        self.assertIn("errors", content)

    def test_bad_limit_max_is_problem_json(self):
        with self.settings(WAGTAILAPI_LIMIT_MAX=5):
            response = self.client.get(
                reverse("wagtailapi_v3:list_pages"),
                {"limit": 100},
            )
        assert_problem_response(self, response, status_code=400)

    def test_unknown_schema_type_is_problem_json(self):
        response = self.client.get(
            reverse(
                "wagtailapi_v3:get_schema_for_type",
                kwargs={"type_name": "unknown"},
            )
        )
        assert_problem_response(self, response, status_code=404)
