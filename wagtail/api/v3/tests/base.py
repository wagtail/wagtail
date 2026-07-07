from django.test import SimpleTestCase

from wagtail.api.v3.errors import PROBLEM_JSON


class TestV3Base(SimpleTestCase):
    def assert_problem_response(self, response, *, status_code, detail_contains=None):
        """
        Assert that a response is an RFC 7807 problem response. Usage:
        ```python
        response = self.client.get(reverse("wagtailapi_v3:list_pages"))
        assert_problem_response(self, response, status_code=400)
        ```
        """
        self.assertEqual(response.status_code, status_code)
        self.assertEqual(response["Content-Type"], PROBLEM_JSON)

        content = response.json()
        self.assertEqual(content["status"], status_code)
        self.assertIn("title", content)
        self.assertIn("type", content)
        self.assertIn("detail", content)

        if detail_contains is not None:
            self.assertIn(detail_contains, content["detail"])

        return content
