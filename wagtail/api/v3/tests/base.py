from django.test import SimpleTestCase

from wagtail.api.v3.errors import PROBLEM_JSON
from wagtail.log_actions import registry as log_registry


class TestV3Base(SimpleTestCase):
    def assert_problem_response(
        self,
        response,
        *,
        status_code,
        detail_contains=None,
        errors=None,
    ):
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

        if errors is not None:
            self.assertTrue(
                all(
                    error.items() <= content["errors"][i].items()
                    for i, error in enumerate(errors)
                ),
                f"Expected errors {errors} to be a subset of "
                f"response errors {content['errors']}",
            )

        return content

    def assert_log_actions(self, instance, actions, since=None):
        logs = log_registry.get_logs_for_instance(instance)
        if since:
            logs = logs.filter(timestamp__gte=since)
        new_actions = list(logs.order_by("timestamp").values_list("action", flat=True))
        self.assertEqual(new_actions, actions)
