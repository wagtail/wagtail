from wagtail.api.v3.errors import PROBLEM_JSON


def assert_problem_response(test_case, response, *, status_code, detail_contains=None):
    """
    Assert that a response is an RFC 7807 problem response. Usage:
    ```python
    response = self.client.get(reverse("wagtailapi_v3:list_pages"))
    assert_problem_response(self, response, status_code=400)
    ```
    """
    test_case.assertEqual(response.status_code, status_code)
    test_case.assertEqual(response["Content-Type"], PROBLEM_JSON)

    content = response.json()
    test_case.assertEqual(content["status"], status_code)
    test_case.assertIn("title", content)
    test_case.assertIn("type", content)
    test_case.assertIn("detail", content)

    if detail_contains is not None:
        test_case.assertIn(detail_contains, content["detail"])

    return content
