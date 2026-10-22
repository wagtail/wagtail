import json
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from wagtail.api.v3.errors import PROBLEM_JSON
from wagtail.log_actions import registry as log_registry
from wagtail.models import (
    APIToken,
    GroupApprovalTask,
    Task,
    Workflow,
    WorkflowPage,
    WorkflowTask,
)
from wagtail.test.testapp.models import SimplePage
from wagtail.test.utils import Page, WagtailTestUtils


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


def delete_existing_workflows():
    """Remove workflows shipped in the initial data, mirroring
    wagtail/admin/tests/test_workflows.py, so tests define their own."""
    WorkflowPage.objects.all().delete()
    Workflow.objects.all().delete()
    Task.objects.all().delete()
    WorkflowTask.objects.all().delete()


class TestV3WorkflowBase(TestV3Base, WagtailTestUtils, TestCase):
    """Shared fixtures for the workflow transition endpoint tests (page half).

    Sets up submitter / moderator / bare approver / superuser users, a
    two-task group-approval workflow, and a draft page assigned to it.
    """

    def setUp(self):
        super().setUp()
        delete_existing_workflows()

        self.submitter = self.create_user(
            username="submitter",
            password="password",  # noqa: S106 - test fixture
        )
        Group.objects.get(name="Editors").user_set.add(self.submitter)  # ty: ignore[unresolved-attribute]
        self.moderator = self.create_user(
            username="moderator",
            password="password",  # noqa: S106 - test fixture
            first_name="Mod",
            last_name="Erator",
        )
        Group.objects.get(name="Moderators").user_set.add(self.moderator)  # ty: ignore[unresolved-attribute]
        self.bare_approver = self.create_user(
            username="bare-approver",
            password="password",  # noqa: S106 - test fixture
        )
        bare_approvers = Group.objects.create(name="Bare approvers")
        self.bare_approver.groups.add(bare_approvers)
        self.superuser = self.create_superuser(
            username="superuser",
            password="password",  # noqa: S106 - test fixture
        )

        self.workflow = Workflow.objects.create(name="test_workflow")
        self.task_1 = GroupApprovalTask.objects.create(name="test_task_1")
        self.task_2 = GroupApprovalTask.objects.create(name="test_task_2")
        for i, task in enumerate((self.task_1, self.task_2), start=1):
            task.groups.set(
                Group.objects.filter(name__in=["Moderators", "Bare approvers"])
            )
            WorkflowTask.objects.create(workflow=self.workflow, task=task, sort_order=i)

        self.home_page = Page.objects.get(depth=2)
        self.page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            content="hello",
            live=False,
        )
        self.home_page.add_child(instance=self.page)
        WorkflowPage.objects.create(workflow=self.workflow, page=self.page)
        self.page.save_revision(user=self.submitter)

    def post_workflow(self, transition, page, data=None):
        """POST to the page workflow transition endpoint, sending ``data`` as
        the JSON body (an empty object by default)."""
        return self.client.post(
            reverse(
                f"wagtailapi_v3:pages_actions_workflow_{transition}",
                kwargs={"page_id": page.pk},
            ),
            data=json.dumps(data or {}),
            content_type="application/json",
        )
