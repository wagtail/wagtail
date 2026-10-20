import json
from unittest import mock

from django.contrib.admin.utils import quote
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from wagtail.api.v3.tests.base import TestV3WorkflowBase
from wagtail.models import (
    TaskState,
    WorkflowContentType,
    WorkflowState,
    WorkflowTask,
)
from wagtail.test.testapp.models import FullFeaturedSnippet


class TestV3SnippetWorkflowBase(TestV3WorkflowBase):
    """Snippet half of the shared workflow fixtures: a draft
    ``FullFeaturedSnippet`` assigned to the two-task workflow, plus snippet
    edit/publish permissions for the submitter and moderator."""

    type_label = "tests.FullFeaturedSnippet"

    def setUp(self):
        super().setUp()
        self.snippet = FullFeaturedSnippet.objects.create(
            text="Hello world!", live=False
        )
        WorkflowContentType.objects.create(
            workflow=self.workflow,
            content_type=ContentType.objects.get_for_model(FullFeaturedSnippet),
        )
        self.snippet.save_revision(user=self.submitter)
        edit_permission = Permission.objects.get(
            content_type__app_label="tests",
            codename="change_fullfeaturedsnippet",
        )
        publish_permission = Permission.objects.get(
            content_type__app_label="tests",
            codename="publish_fullfeaturedsnippet",
        )
        self.submitter.user_permissions.add(edit_permission)
        self.moderator.user_permissions.add(edit_permission, publish_permission)

    def make_workflow_snippet(self, text):
        snippet = FullFeaturedSnippet.objects.create(text=text, live=False)
        snippet.save_revision(user=self.submitter)
        return snippet

    def post_workflow(self, transition, page, data=None):
        """POST to the snippet workflow transition endpoint, sending ``data``
        as the JSON body (an empty object by default).

        The ``page`` parameter name matches
        ``TestV3WorkflowBase.post_workflow`` (which this class extends, and
        which ty holds this override's signature to); here it receives the
        snippet under test."""
        return self.client.post(
            reverse(
                f"wagtailapi_v3:snippets_actions_workflow_{transition}",
                kwargs={"type": self.type_label, "pk": quote(page.pk)},
            ),
            data=json.dumps(data or {}),
            content_type="application/json",
        )

    def login_as(self, user_fixture):
        """Switch auth to a named user fixture; ``None`` means anonymous."""
        if user_fixture is None:
            self.unauthorize()
            return None
        user = getattr(self, user_fixture)
        self.login(user=user)
        return user

    def assert_workflow_state_error(self, response, msg):
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[{"type": "workflow_state_error", "msg": msg}],
        )


class TestSnippetWorkflowTransitions(TestV3SnippetWorkflowBase, TestCase):
    def setUp(self):
        super().setUp()
        # No snippet permissions, no task-group membership: excluded from
        # submit/resume by the edit-permission gate and from approve/reject
        # by the task-group gate.
        self.outsider = self.create_user(username="outsider", password="password")

    # Happy paths

    def test_submit_returns_workflow_status(self):
        self.login(user=self.submitter)
        response = self.post_workflow("submit", self.snippet)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["workflow"]["name"], "test_workflow")
        self.assertEqual(content["workflow_state"]["status"], "in_progress")
        self.assertEqual(
            content["workflow_state"]["requested_by"]["username"],
            self.submitter.get_username(),
        )
        self.assertEqual(
            content["workflow_state"]["current_task_state"]["status"], "in_progress"
        )
        tasks = content["workflow_state"]["tasks"]
        self.assertEqual(tasks[0]["task"]["name"], "test_task_1")
        self.assertEqual(tasks[0]["task_state"]["status"], "in_progress")
        self.assertIsNone(tasks[1]["task_state"])
        self.assertEqual(content["allowed_actions"], ["cancel"])

    def test_approve_mid_workflow_moves_to_next_task(self):
        self.login(user=self.submitter)
        self.post_workflow("submit", self.snippet)
        self.login(user=self.moderator)
        response = self.post_workflow("approve", self.snippet)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["workflow_state"]["status"], "in_progress")
        current_task_state = content["workflow_state"]["current_task_state"]
        tasks = content["workflow_state"]["tasks"]
        self.assertEqual(current_task_state["id"], tasks[1]["task_state"]["id"])
        self.assertEqual(tasks[1]["task"]["name"], "test_task_2")
        self.assertEqual(content["allowed_actions"], ["approve", "reject", "cancel"])

    def test_approve_final_task_publishes_snippet(self):
        self.login(user=self.submitter)
        self.post_workflow("submit", self.snippet)
        self.login(user=self.moderator)
        self.post_workflow("approve", self.snippet)
        response = self.post_workflow("approve", self.snippet)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["workflow_state"]["status"], "approved")
        self.assertEqual(content["allowed_actions"], ["submit"])
        self.snippet.refresh_from_db()
        self.assertTrue(self.snippet.live)

    def test_reject_records_comment_and_requests_changes(self):
        self.login(user=self.submitter)
        self.post_workflow("submit", self.snippet)
        self.login(user=self.moderator)
        response = self.post_workflow(
            "reject", self.snippet, {"comment": "Please fix the intro"}
        )
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["workflow_state"]["status"], "needs_changes")
        task_states = content["workflow_state"]["task_states"]
        self.assertEqual(task_states[-1]["status"], "rejected")
        self.assertEqual(task_states[-1]["comment"], "Please fix the intro")
        self.assertEqual(
            task_states[-1]["finished_by"]["username"], self.moderator.get_username()
        )
        self.assertEqual(content["allowed_actions"], ["resume"])

    def test_resume_returns_workflow_to_in_progress(self):
        self.login(user=self.submitter)
        self.post_workflow("submit", self.snippet)
        self.login(user=self.moderator)
        self.post_workflow("reject", self.snippet)
        self.login(user=self.submitter)
        response = self.post_workflow("resume", self.snippet)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["workflow_state"]["status"], "in_progress")
        current_task_state = content["workflow_state"]["current_task_state"]
        tasks = content["workflow_state"]["tasks"]
        self.assertEqual(current_task_state["id"], tasks[0]["task_state"]["id"])
        self.assertEqual(tasks[0]["task"]["name"], "test_task_1")
        self.assertEqual(current_task_state["status"], "in_progress")
        self.assertEqual(content["allowed_actions"], ["cancel"])

    def test_cancel_sets_workflow_cancelled(self):
        self.login(user=self.submitter)
        self.post_workflow("submit", self.snippet)
        response = self.post_workflow("cancel", self.snippet)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["workflow_state"]["status"], "cancelled")
        self.assertEqual(
            [ts["status"] for ts in content["workflow_state"]["task_states"]],
            ["cancelled"],
        )
        self.assertEqual(content["allowed_actions"], ["submit"])

    def test_submit_live_unchanged_snippet(self):
        # Admin parity: a live snippet without unpublished changes
        # can still be submitted into moderation.
        self.snippet.live = True
        self.snippet.save()
        self.login(user=self.submitter)
        response = self.post_workflow("submit", self.snippet)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["workflow_state"]["status"], "in_progress")

    def test_submit_snippet_without_revision(self):
        snippet = FullFeaturedSnippet.objects.create(text="No revision", live=False)
        self.login(user=self.submitter)
        response = self.post_workflow("submit", snippet)
        self.assertEqual(response.status_code, 200)
        snippet.refresh_from_db()
        revision = snippet.get_latest_revision()
        self.assertIsNotNone(revision)
        self.assertEqual(
            response.json()["workflow_state"]["current_task_state"]["revision_id"],
            revision.id,
        )

    # Permission matrix per transition

    def test_submit_permission_matrix(self):
        # Submitting requires snippet edit permission; anonymous gets 401.
        matrix = [
            (None, 401),
            ("outsider", 403),
            ("moderator", 200),
            ("superuser", 200),
        ]
        for i, (user_fixture, expected_status) in enumerate(matrix):
            with self.subTest(user=user_fixture, expected_status=expected_status):
                snippet = self.make_workflow_snippet(f"submit-matrix-{i}")
                self.login_as(user_fixture)
                response = self.post_workflow("submit", snippet)
                self.assertEqual(response.status_code, expected_status)
                if expected_status == 200:
                    self.assertEqual(
                        response.json()["workflow_state"]["status"], "in_progress"
                    )

    def test_approve_permission_matrix(self):
        # Approving requires membership of the current task's group, not
        # snippet permissions (a bare approver must get 200).
        matrix = [
            (None, 401),
            ("outsider", 403),
            ("submitter", 403),
            ("bare_approver", 200),
            ("superuser", 200),
        ]
        for i, (user_fixture, expected_status) in enumerate(matrix):
            with self.subTest(user=user_fixture, expected_status=expected_status):
                snippet = self.make_workflow_snippet(f"approve-matrix-{i}")
                self.login(user=self.submitter)
                self.post_workflow("submit", snippet)
                self.login_as(user_fixture)
                response = self.post_workflow("approve", snippet)
                self.assertEqual(response.status_code, expected_status)
                if expected_status == 200:
                    content = response.json()
                    # Two-task workflow: the first approval never reaches the
                    # final publish, so the workflow stays in progress.
                    self.assertEqual(content["workflow_state"]["status"], "in_progress")
                    tasks = content["workflow_state"]["tasks"]
                    self.assertEqual(tasks[1]["task"]["name"], "test_task_2")
                    self.assertEqual(
                        content["workflow_state"]["current_task_state"]["id"],
                        tasks[1]["task_state"]["id"],
                    )

    def test_reject_permission_matrix(self):
        matrix = [
            (None, 401),
            ("outsider", 403),
            ("bare_approver", 200),
            ("superuser", 200),
        ]
        for i, (user_fixture, expected_status) in enumerate(matrix):
            with self.subTest(user=user_fixture, expected_status=expected_status):
                snippet = self.make_workflow_snippet(f"reject-matrix-{i}")
                self.login(user=self.submitter)
                self.post_workflow("submit", snippet)
                self.login_as(user_fixture)
                response = self.post_workflow("reject", snippet)
                self.assertEqual(response.status_code, expected_status)
                if expected_status == 200:
                    self.assertEqual(
                        response.json()["workflow_state"]["status"], "needs_changes"
                    )

    def test_resume_permission_matrix(self):
        # Resuming requires snippet edit permission (the caller acts as
        # editor).
        matrix = [
            (None, 401),
            ("outsider", 403),
            ("submitter", 200),
            ("moderator", 200),
            ("superuser", 200),
        ]
        for i, (user_fixture, expected_status) in enumerate(matrix):
            with self.subTest(user=user_fixture, expected_status=expected_status):
                snippet = self.make_workflow_snippet(f"resume-matrix-{i}")
                self.login(user=self.submitter)
                self.post_workflow("submit", snippet)
                self.login(user=self.moderator)
                self.post_workflow("reject", snippet)
                self.login_as(user_fixture)
                response = self.post_workflow("resume", snippet)
                self.assertEqual(response.status_code, expected_status)
                if expected_status == 200:
                    self.assertEqual(
                        response.json()["workflow_state"]["status"], "in_progress"
                    )

    def test_cancel_permission_matrix(self):
        # Cancelling is allowed for the requester, the snippet editor, and
        # users who can act on the current task; unrelated users get 403.
        matrix = [
            (None, 401),
            ("outsider", 403),
            ("submitter", 200),
            ("moderator", 200),
            ("superuser", 200),
        ]
        for i, (user_fixture, expected_status) in enumerate(matrix):
            with self.subTest(user=user_fixture, expected_status=expected_status):
                snippet = self.make_workflow_snippet(f"cancel-matrix-{i}")
                self.login(user=self.submitter)
                self.post_workflow("submit", snippet)
                self.login_as(user_fixture)
                response = self.post_workflow("cancel", snippet)
                self.assertEqual(response.status_code, expected_status)
                if expected_status == 200:
                    self.assertEqual(
                        response.json()["workflow_state"]["status"], "cancelled"
                    )

    # Final-approval publish permission

    def test_final_approval_without_publish_permission_returns_403(self):
        WorkflowTask.objects.get(workflow=self.workflow, task=self.task_2).delete()
        user = self.create_user(username="editor-approver", password="password")
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="tests",
                codename="change_fullfeaturedsnippet",
            )
        )
        user.groups.add(Group.objects.get(name="Bare approvers"))

        self.login(user=self.submitter)
        self.post_workflow("submit", self.snippet)
        self.login(user=user)
        since = timezone.now()
        response = self.post_workflow("approve", self.snippet)
        self.assert_problem_response(response, status_code=403)

        # The approval rolled back: the workflow state stays in progress and
        # the task state is unchanged, with no log entries.
        state = self.snippet.workflow_states.get()
        self.assertEqual(state.status, WorkflowState.STATUS_IN_PROGRESS)
        task_state = state.current_task_state
        task_state.refresh_from_db()
        self.assertEqual(task_state.status, TaskState.STATUS_IN_PROGRESS)
        self.assert_log_actions(self.snippet, [], since=since)

    # State machine (invalid combinations → 422)

    def test_submit_without_workflow_returns_422(self):
        snippet = self.make_workflow_snippet("no-workflow")
        WorkflowContentType.objects.filter(
            content_type=ContentType.objects.get_for_model(FullFeaturedSnippet)
        ).delete()
        self.login(user=self.submitter)
        response = self.post_workflow("submit", snippet)
        self.assert_workflow_state_error(
            response, "There is no active workflow assigned to this object."
        )

    def test_submit_while_in_progress_returns_422(self):
        # Acted as a task-group member: the workflow lock locks out the
        # submitter itself (see the locked-snippet tests below).
        self.login(user=self.submitter)
        self.post_workflow("submit", self.snippet)
        self.login(user=self.moderator)
        response = self.post_workflow("submit", self.snippet)
        self.assert_workflow_state_error(
            response, "A workflow is already active on this object."
        )

    def test_submit_while_needs_changes_returns_422(self):
        # A rejected workflow has no current task, so no workflow lock applies
        # and the submitter may make the call.
        self.login(user=self.submitter)
        self.post_workflow("submit", self.snippet)
        self.login(user=self.moderator)
        self.post_workflow("reject", self.snippet)
        self.login(user=self.submitter)
        response = self.post_workflow("submit", self.snippet)
        self.assert_workflow_state_error(
            response, "A workflow is already active on this object."
        )

    def test_approve_and_reject_without_active_state_return_422(self):
        snippet = self.make_workflow_snippet("no-active-state")
        self.login(user=self.moderator)
        for transition in ("approve", "reject"):
            with self.subTest(transition=transition):
                response = self.post_workflow(transition, snippet)
                self.assert_workflow_state_error(
                    response, "This object is not currently awaiting moderation."
                )

    def test_approve_with_stale_prior_task_state_id_returns_422(self):
        # approve and reject share resolve_task_state, so both are checked.
        self.login(user=self.submitter)
        self.post_workflow("submit", self.snippet)
        stale_id = self.snippet.current_workflow_state.current_task_state.id
        self.login(user=self.moderator)
        self.post_workflow("reject", self.snippet)
        self.post_workflow("resume", self.snippet)
        for transition in ("approve", "reject"):
            with self.subTest(transition=transition):
                response = self.post_workflow(
                    transition, self.snippet, {"task_state_id": stale_id}
                )
                self.assert_workflow_state_error(
                    response,
                    "The provided task_state_id does not match the object's "
                    "current task state.",
                )

    def test_approve_with_next_task_state_id_returns_422(self):
        self.login(user=self.submitter)
        self.post_workflow("submit", self.snippet)
        state = self.snippet.current_workflow_state
        next_task_state = TaskState.objects.create(
            workflow_state=state,
            revision=state.current_task_state.revision,
            task=self.task_2,
        )
        self.login(user=self.moderator)
        response = self.post_workflow(
            "approve", self.snippet, {"task_state_id": next_task_state.id}
        )
        self.assert_workflow_state_error(
            response,
            "The provided task_state_id does not match the object's current "
            "task state.",
        )

    def test_approve_with_task_state_id_from_another_snippet_returns_422(self):
        other_snippet = self.make_workflow_snippet("other-workflow-snippet")
        self.login(user=self.submitter)
        self.post_workflow("submit", self.snippet)
        self.post_workflow("submit", other_snippet)
        other_task_state_id = other_snippet.current_workflow_state.current_task_state.id
        self.login(user=self.moderator)
        response = self.post_workflow(
            "approve", self.snippet, {"task_state_id": other_task_state_id}
        )
        self.assert_workflow_state_error(
            response,
            "The provided task_state_id does not match the object's current "
            "task state.",
        )

    def test_approve_on_approved_workflow_returns_422(self):
        WorkflowTask.objects.get(workflow=self.workflow, task=self.task_2).delete()
        self.login(user=self.submitter)
        self.post_workflow("submit", self.snippet)
        self.login(user=self.moderator)
        self.assertEqual(self.post_workflow("approve", self.snippet).status_code, 200)
        response = self.post_workflow("approve", self.snippet)
        self.assert_workflow_state_error(
            response, "This object is not currently awaiting moderation."
        )

    def test_resume_while_in_progress_returns_422(self):
        self.login(user=self.submitter)
        self.post_workflow("submit", self.snippet)
        self.login(user=self.moderator)
        response = self.post_workflow("resume", self.snippet)
        self.assert_workflow_state_error(
            response, "The workflow on this object is not awaiting changes."
        )

    def test_cancel_without_active_state_returns_422(self):
        snippet = self.make_workflow_snippet("never-submitted")
        self.login(user=self.submitter)
        response = self.post_workflow("cancel", snippet)
        self.assert_workflow_state_error(
            response, "There is no active workflow on this object to cancel."
        )

    def test_transitions_without_active_state_check_permission_first(self):
        snippet = self.make_workflow_snippet("no-active-state")
        self.login(user=self.outsider)
        for transition in ("approve", "reject", "cancel"):
            with self.subTest(transition=transition):
                response = self.post_workflow(transition, snippet)
                self.assert_problem_response(response, status_code=403)

    # Locked snippet

    def test_submit_while_locked_out_by_workflow_returns_403(self):
        # While the workflow is in progress the submitter is outside the
        # current task's group, so the workflow lock applies (403, not 422).
        self.login(user=self.submitter)
        self.post_workflow("submit", self.snippet)
        response = self.post_workflow("submit", self.snippet)
        self.assert_problem_response(
            response,
            status_code=403,
            detail_contains="is locked.",
        )

    def test_resume_locked_snippet_returns_403(self):
        self.login(user=self.submitter)
        self.post_workflow("submit", self.snippet)
        self.login(user=self.moderator)
        self.post_workflow("reject", self.snippet)
        # In needs_changes there is no workflow lock, but a manually locked
        # snippet still excludes users other than the locker.
        self.snippet.locked = True
        self.snippet.locked_by = self.moderator
        self.snippet.save()
        self.login(user=self.submitter)
        response = self.post_workflow("resume", self.snippet)
        self.assert_problem_response(
            response,
            status_code=403,
            detail_contains="is locked.",
        )

    # Audit log sequences

    def test_submit_logging(self):
        self.login(user=self.submitter)
        since = timezone.now()
        response = self.post_workflow("submit", self.snippet)
        self.assertEqual(response.status_code, 200)
        self.assert_log_actions(self.snippet, ["wagtail.workflow.start"], since=since)

    def test_final_approval_logging(self):
        self.login(user=self.submitter)
        self.post_workflow("submit", self.snippet)
        self.login(user=self.moderator)
        self.post_workflow("approve", self.snippet)
        since = timezone.now()
        response = self.post_workflow("approve", self.snippet)
        self.assertEqual(response.status_code, 200)
        self.assert_log_actions(
            self.snippet,
            ["wagtail.workflow.approve", "wagtail.publish"],
            since=since,
        )

    def test_reject_logging(self):
        self.login(user=self.submitter)
        self.post_workflow("submit", self.snippet)
        self.login(user=self.moderator)
        since = timezone.now()
        response = self.post_workflow("reject", self.snippet)
        self.assertEqual(response.status_code, 200)
        self.assert_log_actions(self.snippet, ["wagtail.workflow.reject"], since=since)

    def test_resume_logging(self):
        self.login(user=self.submitter)
        self.post_workflow("submit", self.snippet)
        self.login(user=self.moderator)
        self.post_workflow("reject", self.snippet)
        self.login(user=self.submitter)
        since = timezone.now()
        response = self.post_workflow("resume", self.snippet)
        self.assertEqual(response.status_code, 200)
        self.assert_log_actions(self.snippet, ["wagtail.workflow.resume"], since=since)

    def test_cancel_logging(self):
        # TaskState.cancel() logs nothing; WorkflowState.cancel() logs once.
        self.login(user=self.submitter)
        self.post_workflow("submit", self.snippet)
        since = timezone.now()
        response = self.post_workflow("cancel", self.snippet)
        self.assertEqual(response.status_code, 200)
        self.assert_log_actions(self.snippet, ["wagtail.workflow.cancel"], since=since)

    # Settings interplay

    @override_settings(WAGTAIL_WORKFLOW_ENABLED=False)
    def test_workflow_disabled_submit_returns_422(self):
        self.login(user=self.submitter)
        response = self.post_workflow("submit", self.snippet)
        self.assert_workflow_state_error(
            response, "There is no active workflow assigned to this object."
        )

    def test_cancel_on_publish_cancels_workflow(self):
        self.login(user=self.submitter)
        self.post_workflow("submit", self.snippet)
        self.login(user=self.moderator)
        response = self.client.post(
            reverse(
                "wagtailapi_v3:snippets_actions_publish",
                kwargs={"type": self.type_label, "pk": quote(self.snippet.pk)},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.snippet.workflow_states.get().status,
            WorkflowState.STATUS_CANCELLED,
        )

    @override_settings(WAGTAIL_WORKFLOW_CANCEL_ON_PUBLISH=False)
    def test_cancel_on_publish_disabled_keeps_workflow_active(self):
        self.login(user=self.submitter)
        self.post_workflow("submit", self.snippet)
        self.login(user=self.moderator)
        response = self.client.post(
            reverse(
                "wagtailapi_v3:snippets_actions_publish",
                kwargs={"type": self.type_label, "pk": quote(self.snippet.pk)},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.snippet.workflow_states.get().status,
            WorkflowState.STATUS_IN_PROGRESS,
        )

    def test_custom_finish_action_completes_without_publishing(self):
        # WAGTAIL_FINISH_WORKFLOW_ACTION is evaluated at import time, so the
        # custom finish is exercised by patching WorkflowState.on_finish.
        WorkflowTask.objects.get(workflow=self.workflow, task=self.task_2).delete()
        self.login(user=self.submitter)
        self.post_workflow("submit", self.snippet)
        self.login(user=self.moderator)
        with mock.patch.object(WorkflowState, "on_finish") as on_finish:
            response = self.post_workflow("approve", self.snippet)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["workflow_state"]["status"], "approved")
        on_finish.assert_called_once()
        self.snippet.refresh_from_db()
        self.assertFalse(self.snippet.live)

    @override_settings(WAGTAIL_WORKFLOW_REQUIRE_REAPPROVAL_ON_EDIT=True)
    def test_reapproval_on_edit_only_reuses_states_on_current_revision(self):
        self.login(user=self.submitter)
        self.post_workflow("submit", self.snippet)
        self.login(user=self.moderator)
        self.post_workflow("approve", self.snippet)  # task 1 approved, task 2 current
        self.post_workflow("reject", self.snippet)  # needs_changes
        self.login(user=self.submitter)
        self.snippet.text = "Edited"
        self.snippet.save_revision(user=self.submitter)
        response = self.post_workflow("resume", self.snippet)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["workflow_state"]["status"], "in_progress")
        self.assertEqual(
            content["workflow_state"]["current_task_state"]["status"], "in_progress"
        )
        self.assertEqual(
            content["workflow_state"]["tasks"][1]["task"]["name"], "test_task_2"
        )
        self.assertEqual(
            content["workflow_state"]["tasks"][1]["task_state"]["status"],
            "in_progress",
        )
        self.assertIsNone(content["workflow_state"]["tasks"][0]["task_state"])
        # Task 1's approval was made on the previous revision, so it no longer
        # applies; only the restarted task 2 has a state on the new revision.
        tasks = content["workflow_state"]["tasks"]
        self.assertIsNone(tasks[0]["task_state"])
        self.assertEqual(tasks[1]["task_state"]["status"], "in_progress")


class WorkflowReadsMixin:
    """Request helpers for the workflow status and history read endpoints."""

    # Annotated for type checkers: the mixin itself is not a TestCase, but
    # every host class provides the Django test client.
    client: Client

    def get_status(self, snippet):
        return self.client.get(
            reverse(
                "wagtailapi_v3:snippets_workflow_status",
                kwargs={"type": TestV3SnippetWorkflowBase.type_label, "pk": snippet.pk},
            )
        )

    def get_history(self, snippet, data=None):
        return self.client.get(
            reverse(
                "wagtailapi_v3:snippets_workflow_history",
                kwargs={
                    "type": TestV3SnippetWorkflowBase.type_label,
                    "pk": quote(snippet.pk),
                },
            ),
            data=data,
        )


class TestSnippetWorkflowReads(WorkflowReadsMixin, TestV3SnippetWorkflowBase, TestCase):
    def setUp(self):
        super().setUp()
        # No snippet permissions and no task-group membership: never passes
        # the workflow read gate.
        self.outsider = self.create_user(username="outsider", password="password")

    def submit_snippet(self):
        self.login(user=self.submitter)
        response = self.post_workflow("submit", self.snippet)
        self.assertEqual(response.status_code, 200)

    # Payload shape

    def test_status_in_progress_payload_shape_per_caller(self):
        self.submit_snippet()

        # A moderator (task-group member with edit permission).
        self.login(user=self.moderator)
        response = self.get_status(self.snippet)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["workflow"]["name"], "test_workflow")
        self.assertEqual(content["workflow_state"]["status"], "in_progress")
        self.assertEqual(
            content["workflow_state"]["requested_by"]["username"],
            self.submitter.get_username(),
        )
        self.assertEqual(
            content["workflow_state"]["current_task_state"]["status"], "in_progress"
        )
        tasks = content["workflow_state"]["tasks"]
        self.assertEqual(tasks[0]["task"]["name"], "test_task_1")
        self.assertEqual(tasks[0]["task_state"]["status"], "in_progress")
        self.assertEqual(tasks[1]["task"]["name"], "test_task_2")
        # The second task has not started yet.
        self.assertIsNone(tasks[1]["task_state"])
        self.assertEqual(content["allowed_actions"], ["approve", "reject", "cancel"])

        # A task-group member without snippet edit permission sees the same
        # actions: they are granted by the task, not by snippet permissions.
        self.login(user=self.bare_approver)
        content = self.get_status(self.snippet).json()
        self.assertEqual(content["allowed_actions"], ["approve", "reject", "cancel"])

        # The submitter is locked out of submit while the workflow is in
        # progress, but may cancel the workflow they requested.
        self.login(user=self.submitter)
        content = self.get_status(self.snippet).json()
        self.assertEqual(content["allowed_actions"], ["cancel"])

    def test_status_in_progress_editor_without_actions_sees_empty_list(self):
        # An editor who is neither the requester, the snippet owner, nor a
        # current task-group member passes the read gate but has no
        # available workflow actions.
        editor = self.create_user(username="plain-editor", password="password")
        editor.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="tests",
                codename="change_fullfeaturedsnippet",
            )
        )
        self.submit_snippet()
        self.login(user=editor)
        response = self.get_status(self.snippet)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["allowed_actions"], [])

    def test_status_fresh_snippet(self):
        # No workflow has been started: there is no state yet and the editor
        # may submit. The assigned (but not started) workflow is reported.
        self.login(user=self.submitter)
        response = self.get_status(self.snippet)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["workflow"]["name"], "test_workflow")
        self.assertIsNone(content["workflow_state"])
        self.assertEqual(content["allowed_actions"], ["submit"])

    def test_status_fresh_snippet_denied_without_edit_permission(self):
        # A user without snippet edit permission and with no active workflow
        # has no read-gate branch that admits them: task actions only exist
        # once the workflow is in progress.
        self.login(user=self.bare_approver)
        self.assert_problem_response(self.get_status(self.snippet), status_code=403)
        self.login(user=self.outsider)
        self.assert_problem_response(self.get_status(self.snippet), status_code=403)

    def test_status_after_cancel_shows_cancelled_state_and_submit(self):
        self.submit_snippet()
        self.login(user=self.submitter)
        self.assertEqual(self.post_workflow("cancel", self.snippet).status_code, 200)
        response = self.get_status(self.snippet)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["workflow_state"]["status"], "cancelled")
        # No active state and the submitter can edit, so submit is available
        # again.
        self.assertEqual(content["allowed_actions"], ["submit"])

    @override_settings(WAGTAIL_WORKFLOW_ENABLED=False)
    def test_status_workflow_disabled_reports_nulls(self):
        self.login(user=self.submitter)
        response = self.get_status(self.snippet)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertIsNone(content["workflow"])
        self.assertIsNone(content["workflow_state"])
        self.assertEqual(content["allowed_actions"], [])

    # Read gate

    def test_status_read_gate_matrix(self):
        # Editors pass, the current task's group members pass, everyone else
        # gets 403, anonymous gets 401.
        self.submit_snippet()
        matrix = [
            (None, 401),
            ("outsider", 403),
            ("submitter", 200),
            ("bare_approver", 200),
            ("moderator", 200),
            ("superuser", 200),
        ]
        for user_fixture, expected_status in matrix:
            with self.subTest(user=user_fixture, expected_status=expected_status):
                if user_fixture is None:
                    self.unauthorize()
                else:
                    self.login(user=getattr(self, user_fixture))
                response = self.get_status(self.snippet)
                self.assertEqual(response.status_code, expected_status)
                if expected_status == 200:
                    self.assertEqual(
                        response.json()["workflow_state"]["status"], "in_progress"
                    )

    def test_status_unknown_snippet_returns_404(self):
        self.login(user=self.submitter)
        last_id = (
            FullFeaturedSnippet.objects.order_by("-id")
            .values_list("id", flat=True)
            .first()
        )
        assert last_id is not None
        response = self.client.get(
            reverse(
                "wagtailapi_v3:snippets_workflow_status",
                kwargs={
                    "type": self.type_label,
                    "pk": last_id + 1,
                },
            )
        )
        self.assert_problem_response(response, status_code=404)


class TestSnippetWorkflowHistory(
    WorkflowReadsMixin, TestV3SnippetWorkflowBase, TestCase
):
    def setUp(self):
        super().setUp()
        self.outsider = self.create_user(username="outsider", password="password")

    def submit_and_cancel(self):
        self.login(user=self.submitter)
        self.assertEqual(self.post_workflow("submit", self.snippet).status_code, 200)
        self.assertEqual(self.post_workflow("cancel", self.snippet).status_code, 200)

    def test_history_on_fresh_snippet_is_empty(self):
        self.login(user=self.submitter)
        response = self.get_history(self.snippet)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"count": 0, "items": []})

    def test_history_pagination_newest_first_and_scope(self):
        self.submit_and_cancel()
        # Cancel the second run too, so the snippet ends with two states: the
        # newest in progress (cancelled second) is listed first.
        self.submit_and_cancel()
        response = self.get_history(self.snippet)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["count"], 2)
        self.assertEqual(len(content["items"]), 2)
        ids = [item["id"] for item in content["items"]]
        self.assertEqual(ids, sorted(ids, reverse=True))
        self.assertEqual(
            [item["status"] for item in content["items"]],
            ["cancelled", "cancelled"],
        )
        # Only this snippet's states are returned.
        self.assertEqual(
            set(ids),
            set(self.snippet.workflow_states.values_list("id", flat=True)),
        )

        # Limit/offset pagination honours the envelope.
        content = self.get_history(self.snippet, {"limit": 1}).json()
        self.assertEqual(content["count"], 2)
        self.assertEqual(len(content["items"]), 1)
        self.assertEqual(content["items"][0]["id"], ids[0])

    def test_history_items_are_lean(self):
        self.submit_and_cancel()
        self.login(user=self.submitter)
        items = self.get_history(self.snippet).json()["items"]
        for item in items:
            # Each item carries the task states it aggregates, but not the
            # workflow's full task timeline (that lives on the status
            # endpoint only).
            self.assertIn("task_states", item)
            self.assertNotIn("tasks", item)

    def test_history_task_states_include_task(self):
        self.login(user=self.submitter)
        self.assertEqual(self.post_workflow("submit", self.snippet).status_code, 200)
        self.login(user=self.moderator)
        self.assertEqual(self.post_workflow("approve", self.snippet).status_code, 200)
        items = self.get_history(self.snippet).json()["items"]
        self.assertEqual(
            [
                (task_state["task"], task_state["status"])
                for task_state in items[0]["task_states"]
            ],
            [
                (
                    {
                        "id": self.task_1.id,
                        "name": "test_task_1",
                        "type": "wagtailcore.GroupApprovalTask",
                    },
                    "approved",
                ),
                (
                    {
                        "id": self.task_2.id,
                        "name": "test_task_2",
                        "type": "wagtailcore.GroupApprovalTask",
                    },
                    "in_progress",
                ),
            ],
        )

    def test_history_read_gate(self):
        self.submit_and_cancel()
        matrix = [
            (None, 401),
            ("outsider", 403),
            ("submitter", 200),
            ("bare_approver", 403),
        ]
        for user_fixture, expected_status in matrix:
            with self.subTest(user=user_fixture, expected_status=expected_status):
                if user_fixture is None:
                    self.unauthorize()
                else:
                    self.login(user=getattr(self, user_fixture))
                response = self.get_history(self.snippet)
                self.assertEqual(response.status_code, expected_status)

    def test_history_unknown_snippet_returns_404(self):
        self.login(user=self.submitter)
        last_id = (
            FullFeaturedSnippet.objects.order_by("-id")
            .values_list("id", flat=True)
            .first()
        )
        assert last_id is not None
        response = self.client.get(
            reverse(
                "wagtailapi_v3:snippets_workflow_history",
                kwargs={"type": self.type_label, "pk": last_id + 1},
            )
        )
        self.assert_problem_response(response, status_code=404)
