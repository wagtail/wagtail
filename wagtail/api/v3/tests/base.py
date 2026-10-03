from typing import Any

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase

from wagtail.api.v3.errors import PROBLEM_JSON
from wagtail.log_actions import registry as log_registry
from wagtail.models import APIToken


class TestV3Base(SimpleTestCase):
    def authorize(self, user, *, name="test token"):
        """Authenticate subsequent self.client calls with a bearer token."""
        token, plaintext = APIToken.create_token(user=user, name=name)
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {plaintext}"
        return token

    def login(self, user=None, username=None, password="password"):  # noqa: S107 - usage in tests allowed
        """v3 API requests authenticate with bearer tokens, not sessions.

        Overrides WagtailTestUtils.login so existing call sites exercise
        token auth: creates (or resolves) the user and authorizes a token.
        """
        user_model: Any = get_user_model()
        if user is None:
            if username is None:
                # Provided by WagtailTestUtils on the concrete test class.
                user = self.create_test_user()  # ty: ignore[unresolved-attribute]
            else:
                if user_model.USERNAME_FIELD == "email" and "@" not in username:
                    username = "%s@example.com" % username
                user = user_model._default_manager.get(
                    **{user_model.USERNAME_FIELD: username}
                )
        self.authorize(user)
        return user

    def unauthorize(self):
        """Stop sending the Authorization header (the token-auth logout)."""
        self.client.defaults.pop("HTTP_AUTHORIZATION", None)

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
