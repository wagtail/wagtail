from unittest import mock

from django.contrib.auth.models import Group, Permission
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from wagtail.api.v3.tests.base import TestV3WorkflowBase
from wagtail.models import (
    GroupPagePermission,
    TaskState,
    WorkflowPage,
    WorkflowState,
    WorkflowTask,
)
from wagtail.test.testapp.models import SimplePage
from wagtail.test.utils import Page


class TestPageWorkflowTransitions(TestV3WorkflowBase, TestCase):
    def setUp(self):
        super().setUp()
        # No page permissions, no task-group membership: excluded from
        # submit/resume by the edit-permission gate and from approve/reject
        # by the task-group gate.
        self.outsider = self.create_user(username="outsider", password="password")

    def make_workflow_page(self, slug):
        page = SimplePage(
            title=slug.replace("-", " ").title(),
            slug=slug,
            content="hello",
            live=False,
        )
        self.home_page.add_child(instance=page)
        WorkflowPage.objects.create(workflow=self.workflow, page=page)
        page.save_revision(user=self.submitter)
        return page

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

    # Happy paths

    def test_submit_returns_workflow_status(self):
        self.login(user=self.submitter)
        response = self.post_workflow("submit", self.page)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["workflow"]["name"], "test_workflow")
        self.assertEqual(content["workflow_state"]["status"], "in_progress")
        self.assertEqual(
            content["workflow_state"]["requested_by"]["username"], "submitter"
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
        self.post_workflow("submit", self.page)
        self.login(user=self.moderator)
        response = self.post_workflow("approve", self.page)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["workflow_state"]["status"], "in_progress")
        current_task_state = content["workflow_state"]["current_task_state"]
        tasks = content["workflow_state"]["tasks"]
        self.assertEqual(current_task_state["id"], tasks[1]["task_state"]["id"])
        self.assertEqual(tasks[1]["task"]["name"], "test_task_2")
        self.assertEqual(content["allowed_actions"], ["approve", "reject", "cancel"])

    def test_approve_final_task_publishes_page(self):
        self.login(user=self.submitter)
        self.post_workflow("submit", self.page)
        self.login(user=self.moderator)
        self.post_workflow("approve", self.page)
        response = self.post_workflow("approve", self.page)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["workflow_state"]["status"], "approved")
        self.assertEqual(content["allowed_actions"], ["submit"])
        self.page.refresh_from_db()
        self.assertTrue(self.page.live)

    def test_reject_records_comment_and_requests_changes(self):
        self.login(user=self.submitter)
        self.post_workflow("submit", self.page)
        self.login(user=self.moderator)
        response = self.post_workflow(
            "reject", self.page, {"comment": "Please fix the intro"}
        )
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["workflow_state"]["status"], "needs_changes")
        task_states = content["workflow_state"]["task_states"]
        self.assertEqual(task_states[-1]["status"], "rejected")
        self.assertEqual(task_states[-1]["comment"], "Please fix the intro")
        self.assertEqual(task_states[-1]["finished_by"]["username"], "moderator")
        self.assertEqual(content["allowed_actions"], ["resume"])

    def test_resume_returns_workflow_to_in_progress(self):
        self.login(user=self.submitter)
        self.post_workflow("submit", self.page)
        self.login(user=self.moderator)
        self.post_workflow("reject", self.page)
        self.login(user=self.submitter)
        response = self.post_workflow("resume", self.page)
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
        self.post_workflow("submit", self.page)
        response = self.post_workflow("cancel", self.page)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["workflow_state"]["status"], "cancelled")
        self.assertEqual(
            [ts["status"] for ts in content["workflow_state"]["task_states"]],
            ["cancelled"],
        )
        self.assertEqual(content["allowed_actions"], ["submit"])

    def test_submit_live_unchanged_page(self):
        # Admin parity: a live page without unpublished changes can
        # still be submitted into moderation.
        self.page.live = True
        self.page.save()
        self.login(user=self.submitter)
        response = self.post_workflow("submit", self.page)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["workflow_state"]["status"], "in_progress")

    # Permission matrix per transition

    def test_submit_permission_matrix(self):
        # Submitting requires page edit permission; anonymous gets 401.
        matrix = [
            (None, 401),
            ("outsider", 403),
            ("moderator", 200),
            ("superuser", 200),
        ]
        for i, (user_fixture, expected_status) in enumerate(matrix):
            with self.subTest(user=user_fixture, expected_status=expected_status):
                page = self.make_workflow_page(f"submit-matrix-{i}")
                self.login_as(user_fixture)
                response = self.post_workflow("submit", page)
                self.assertEqual(response.status_code, expected_status)
                if expected_status == 200:
                    self.assertEqual(
                        response.json()["workflow_state"]["status"], "in_progress"
                    )

    def test_approve_permission_matrix(self):
        # Approving requires membership of the current task's group, not page
        # permissions (a bare approver must get 200).
        matrix = [
            (None, 401),
            ("outsider", 403),
            ("submitter", 403),
            ("bare_approver", 200),
            ("superuser", 200),
        ]
        for i, (user_fixture, expected_status) in enumerate(matrix):
            with self.subTest(user=user_fixture, expected_status=expected_status):
                page = self.make_workflow_page(f"approve-matrix-{i}")
                self.login(user=self.submitter)
                self.post_workflow("submit", page)
                self.login_as(user_fixture)
                response = self.post_workflow("approve", page)
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
                page = self.make_workflow_page(f"reject-matrix-{i}")
                self.login(user=self.submitter)
                self.post_workflow("submit", page)
                self.login_as(user_fixture)
                response = self.post_workflow("reject", page)
                self.assertEqual(response.status_code, expected_status)
                if expected_status == 200:
                    self.assertEqual(
                        response.json()["workflow_state"]["status"], "needs_changes"
                    )

    def test_resume_permission_matrix(self):
        # Resuming requires page edit permission (the caller acts as editor).
        matrix = [
            (None, 401),
            ("outsider", 403),
            ("submitter", 200),
            ("moderator", 200),
            ("superuser", 200),
        ]
        for i, (user_fixture, expected_status) in enumerate(matrix):
            with self.subTest(user=user_fixture, expected_status=expected_status):
                page = self.make_workflow_page(f"resume-matrix-{i}")
                self.login(user=self.submitter)
                self.post_workflow("submit", page)
                self.login(user=self.moderator)
                self.post_workflow("reject", page)
                self.login_as(user_fixture)
                response = self.post_workflow("resume", page)
                self.assertEqual(response.status_code, expected_status)
                if expected_status == 200:
                    self.assertEqual(
                        response.json()["workflow_state"]["status"], "in_progress"
                    )

    def test_cancel_permission_matrix(self):
        # Cancelling is allowed for the requester, the page owner, and users
        # who can act on the current task; unrelated users get 403.
        matrix = [
            (None, 401),
            ("outsider", 403),
            ("submitter", 200),
            ("moderator", 200),
            ("superuser", 200),
        ]
        for i, (user_fixture, expected_status) in enumerate(matrix):
            with self.subTest(user=user_fixture, expected_status=expected_status):
                page = self.make_workflow_page(f"cancel-matrix-{i}")
                self.login(user=self.submitter)
                self.post_workflow("submit", page)
                self.login_as(user_fixture)
                response = self.post_workflow("cancel", page)
                self.assertEqual(response.status_code, expected_status)
                if expected_status == 200:
                    self.assertEqual(
                        response.json()["workflow_state"]["status"], "cancelled"
                    )

    # Final-approval publish permission

    def test_final_approval_without_publish_permission_returns_403(self):
        WorkflowTask.objects.get(workflow=self.workflow, task=self.task_2).delete()
        user = self.create_user(username="editor-approver", password="password")
        group = Group.objects.create(name="Editor approvers")
        user.groups.add(group)
        GroupPagePermission.objects.create(
            group=group,
            page=Page.objects.get(depth=1),
            permission=Permission.objects.get(
                content_type__app_label=Page._meta.app_label,
                codename=Page.PERMISSION_CODENAMES.CHANGE,
            ),
        )
        user.groups.add(Group.objects.get(name="Bare approvers"))

        self.login(user=self.submitter)
        self.post_workflow("submit", self.page)
        self.login(user=user)
        since = timezone.now()
        response = self.post_workflow("approve", self.page)
        self.assert_problem_response(response, status_code=403)

        # The approval rolled back: the workflow state stays in progress and
        # the task state is unchanged, with no log entries.
        state = self.page.workflow_states.get()
        self.assertEqual(state.status, WorkflowState.STATUS_IN_PROGRESS)
        task_state = state.current_task_state
        task_state.refresh_from_db()
        self.assertEqual(task_state.status, TaskState.STATUS_IN_PROGRESS)
        self.assert_log_actions(self.page, [], since=since)

    # State machine (invalid combinations → 422)

    def test_submit_without_workflow_returns_422(self):
        page = SimplePage(
            title="No workflow", slug="no-workflow", content="hello", live=False
        )
        self.home_page.add_child(instance=page)
        page.save_revision(user=self.submitter)
        self.login(user=self.submitter)
        response = self.post_workflow("submit", page)
        self.assert_workflow_state_error(
            response, "There is no active workflow assigned to this object."
        )

    def test_submit_while_in_progress_returns_422(self):
        # Acted as a task-group member: the workflow lock locks out the
        # submitter itself (see the locked-page tests below).
        self.login(user=self.submitter)
        self.post_workflow("submit", self.page)
        self.login(user=self.moderator)
        response = self.post_workflow("submit", self.page)
        self.assert_workflow_state_error(
            response, "A workflow is already active on this object."
        )

    def test_submit_while_needs_changes_returns_422(self):
        # A rejected workflow has no current task, so no workflow lock applies
        # and the submitter may make the call.
        self.login(user=self.submitter)
        self.post_workflow("submit", self.page)
        self.login(user=self.moderator)
        self.post_workflow("reject", self.page)
        self.login(user=self.submitter)
        response = self.post_workflow("submit", self.page)
        self.assert_workflow_state_error(
            response, "A workflow is already active on this object."
        )

    def test_approve_and_reject_without_active_state_return_422(self):
        page = self.make_workflow_page("no-active-state")
        self.login(user=self.moderator)
        for transition in ("approve", "reject"):
            with self.subTest(transition=transition):
                response = self.post_workflow(transition, page)
                self.assert_workflow_state_error(
                    response, "This object is not currently awaiting moderation."
                )

    def test_approve_with_stale_prior_task_state_id_returns_422(self):
        # approve and reject share resolve_task_state, so both are checked.
        self.login(user=self.submitter)
        self.post_workflow("submit", self.page)
        stale_id = self.page.current_workflow_state.current_task_state.id
        self.login(user=self.moderator)
        self.post_workflow("reject", self.page)
        self.post_workflow("resume", self.page)
        for transition in ("approve", "reject"):
            with self.subTest(transition=transition):
                response = self.post_workflow(
                    transition, self.page, {"task_state_id": stale_id}
                )
                self.assert_workflow_state_error(
                    response,
                    "The provided task_state_id does not match the object's "
                    "current task state.",
                )

    def test_approve_with_next_task_state_id_returns_422(self):
        self.login(user=self.submitter)
        self.post_workflow("submit", self.page)
        state = self.page.current_workflow_state
        next_task_state = TaskState.objects.create(
            workflow_state=state,
            revision=state.current_task_state.revision,
            task=self.task_2,
        )
        self.login(user=self.moderator)
        response = self.post_workflow(
            "approve", self.page, {"task_state_id": next_task_state.id}
        )
        self.assert_workflow_state_error(
            response,
            "The provided task_state_id does not match the object's current "
            "task state.",
        )

    def test_approve_with_task_state_id_from_another_page_returns_422(self):
        other_page = self.make_workflow_page("other-workflow-page")
        self.login(user=self.submitter)
        self.post_workflow("submit", self.page)
        self.post_workflow("submit", other_page)
        other_task_state_id = other_page.current_workflow_state.current_task_state.id
        self.login(user=self.moderator)
        response = self.post_workflow(
            "approve", self.page, {"task_state_id": other_task_state_id}
        )
        self.assert_workflow_state_error(
            response,
            "The provided task_state_id does not match the object's current "
            "task state.",
        )

    def test_approve_on_approved_workflow_returns_422(self):
        WorkflowTask.objects.get(workflow=self.workflow, task=self.task_2).delete()
        self.login(user=self.submitter)
        self.post_workflow("submit", self.page)
        self.login(user=self.moderator)
        self.assertEqual(self.post_workflow("approve", self.page).status_code, 200)
        response = self.post_workflow("approve", self.page)
        self.assert_workflow_state_error(
            response, "This object is not currently awaiting moderation."
        )

    def test_resume_while_in_progress_returns_422(self):
        self.login(user=self.submitter)
        self.post_workflow("submit", self.page)
        self.login(user=self.moderator)
        response = self.post_workflow("resume", self.page)
        self.assert_workflow_state_error(
            response, "The workflow on this object is not awaiting changes."
        )

    def test_cancel_without_active_state_returns_422(self):
        page = self.make_workflow_page("never-submitted")
        self.login(user=self.submitter)
        response = self.post_workflow("cancel", page)
        self.assert_workflow_state_error(
            response, "There is no active workflow on this object to cancel."
        )

    # Locked page

    def test_submit_while_locked_out_by_workflow_returns_403(self):
        # While the workflow is in progress the submitter is outside the
        # current task's group, so the workflow lock applies (403, not 422).
        self.login(user=self.submitter)
        self.post_workflow("submit", self.page)
        response = self.post_workflow("submit", self.page)
        self.assert_problem_response(response, status_code=403)

    def test_resume_locked_page_returns_403(self):
        self.login(user=self.submitter)
        self.post_workflow("submit", self.page)
        self.login(user=self.moderator)
        self.post_workflow("reject", self.page)
        # In needs_changes there is no workflow lock, but a manually locked
        # page still excludes users other than the locker.
        self.page.locked = True
        self.page.locked_by = self.moderator
        self.page.save()
        self.login(user=self.submitter)
        response = self.post_workflow("resume", self.page)
        self.assert_problem_response(response, status_code=403)

    # Audit log sequences

    def test_submit_logging(self):
        self.login(user=self.submitter)
        since = timezone.now()
        response = self.post_workflow("submit", self.page)
        self.assertEqual(response.status_code, 200)
        self.assert_log_actions(self.page, ["wagtail.workflow.start"], since=since)

    def test_final_approval_logging(self):
        self.login(user=self.submitter)
        self.post_workflow("submit", self.page)
        self.login(user=self.moderator)
        self.post_workflow("approve", self.page)
        since = timezone.now()
        response = self.post_workflow("approve", self.page)
        self.assertEqual(response.status_code, 200)
        self.assert_log_actions(
            self.page,
            ["wagtail.workflow.approve", "wagtail.publish"],
            since=since,
        )

    def test_reject_logging(self):
        self.login(user=self.submitter)
        self.post_workflow("submit", self.page)
        self.login(user=self.moderator)
        since = timezone.now()
        response = self.post_workflow("reject", self.page)
        self.assertEqual(response.status_code, 200)
        self.assert_log_actions(self.page, ["wagtail.workflow.reject"], since=since)

    def test_resume_logging(self):
        self.login(user=self.submitter)
        self.post_workflow("submit", self.page)
        self.login(user=self.moderator)
        self.post_workflow("reject", self.page)
        self.login(user=self.submitter)
        since = timezone.now()
        response = self.post_workflow("resume", self.page)
        self.assertEqual(response.status_code, 200)
        self.assert_log_actions(self.page, ["wagtail.workflow.resume"], since=since)

    def test_cancel_logging(self):
        # TaskState.cancel() logs nothing; WorkflowState.cancel() logs once.
        self.login(user=self.submitter)
        self.post_workflow("submit", self.page)
        since = timezone.now()
        response = self.post_workflow("cancel", self.page)
        self.assertEqual(response.status_code, 200)
        self.assert_log_actions(self.page, ["wagtail.workflow.cancel"], since=since)

    # Settings interplay

    @override_settings(WAGTAIL_WORKFLOW_ENABLED=False)
    def test_workflow_disabled_submit_returns_422(self):
        self.login(user=self.submitter)
        response = self.post_workflow("submit", self.page)
        self.assert_workflow_state_error(
            response, "There is no active workflow assigned to this object."
        )

    def test_cancel_on_publish_cancels_workflow(self):
        self.login(user=self.submitter)
        self.post_workflow("submit", self.page)
        self.login(user=self.moderator)
        response = self.client.post(
            reverse(
                "wagtailapi_v3:pages_actions_publish",
                kwargs={"page_id": self.page.pk},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.page.workflow_states.get().status, WorkflowState.STATUS_CANCELLED
        )

    @override_settings(WAGTAIL_WORKFLOW_CANCEL_ON_PUBLISH=False)
    def test_cancel_on_publish_disabled_keeps_workflow_active(self):
        self.login(user=self.submitter)
        self.post_workflow("submit", self.page)
        self.login(user=self.moderator)
        response = self.client.post(
            reverse(
                "wagtailapi_v3:pages_actions_publish",
                kwargs={"page_id": self.page.pk},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.page.workflow_states.get().status, WorkflowState.STATUS_IN_PROGRESS
        )

    def test_custom_finish_action_completes_without_publishing(self):
        # WAGTAIL_FINISH_WORKFLOW_ACTION is evaluated at import time, so the
        # custom finish is exercised by patching WorkflowState.on_finish.
        WorkflowTask.objects.get(workflow=self.workflow, task=self.task_2).delete()
        self.login(user=self.submitter)
        self.post_workflow("submit", self.page)
        self.login(user=self.moderator)
        with mock.patch.object(WorkflowState, "on_finish") as on_finish:
            response = self.post_workflow("approve", self.page)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["workflow_state"]["status"], "approved")
        on_finish.assert_called_once()
        self.page.refresh_from_db()
        self.assertFalse(self.page.live)

    @override_settings(WAGTAIL_WORKFLOW_REQUIRE_REAPPROVAL_ON_EDIT=True)
    def test_reapproval_on_edit_only_reuses_states_on_current_revision(self):
        self.login(user=self.submitter)
        self.post_workflow("submit", self.page)
        self.login(user=self.moderator)
        self.post_workflow("approve", self.page)  # task 1 approved, task 2 current
        self.post_workflow("reject", self.page)  # needs_changes
        self.login(user=self.submitter)
        self.page.title = "Edited"
        self.page.save_revision(user=self.submitter)
        response = self.post_workflow("resume", self.page)
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
