from unittest import mock

from django.contrib.auth.models import Group, Permission
from django.test import Client, TestCase, override_settings
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

    def test_submit_page_without_revision(self):
        page = SimplePage(title="No revision", slug="no-revision", content="hello")
        self.home_page.add_child(instance=page)
        WorkflowPage.objects.create(workflow=self.workflow, page=page)
        self.login(user=self.submitter)
        response = self.post_workflow("submit", page)
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        revision = page.get_latest_revision()
        self.assertIsNotNone(revision)
        self.assertEqual(
            response.json()["workflow_state"]["current_task_state"]["revision_id"],
            revision.id,
        )

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

    def test_transitions_without_active_state_check_permission_first(self):
        page = self.make_workflow_page("no-active-state")
        self.login(user=self.outsider)
        for transition in ("approve", "reject", "cancel"):
            with self.subTest(transition=transition):
                response = self.post_workflow(transition, page)
                self.assert_problem_response(response, status_code=403)

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


class WorkflowReadsMixin:
    """Request helpers for the workflow status and history read endpoints."""

    # Annotated for type checkers: the mixin itself is not a TestCase, but
    # every host class provides the Django test client.
    client: Client

    def get_status(self, page):
        return self.client.get(
            reverse("wagtailapi_v3:get_page_workflow", kwargs={"page_id": page.pk})
        )

    def get_history(self, page, data=None):
        return self.client.get(
            reverse(
                "wagtailapi_v3:list_page_workflow_history",
                kwargs={"page_id": page.pk},
            ),
            data=data,
        )


class TestPageWorkflowReads(WorkflowReadsMixin, TestV3WorkflowBase, TestCase):
    def setUp(self):
        super().setUp()
        # No page permissions and no task-group membership: never passes the
        # workflow read gate.
        self.outsider = self.create_user(username="outsider", password="password")

    def submit_page(self):
        self.login(user=self.submitter)
        response = self.post_workflow("submit", self.page)
        self.assertEqual(response.status_code, 200)

    # Payload shape

    def test_status_in_progress_payload_shape_per_caller(self):
        self.submit_page()

        # A moderator (task-group member with edit permission).
        self.login(user=self.moderator)
        response = self.get_status(self.page)
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
        self.assertEqual(tasks[1]["task"]["name"], "test_task_2")
        # The second task has not started yet.
        self.assertIsNone(tasks[1]["task_state"])
        self.assertEqual(content["allowed_actions"], ["approve", "reject", "cancel"])

        # A task-group member without edit permission sees the same actions:
        # they are granted by the task, not by page permissions.
        self.login(user=self.bare_approver)
        content = self.get_status(self.page).json()
        self.assertEqual(content["allowed_actions"], ["approve", "reject", "cancel"])

        # The submitter is locked out of submit while the workflow is in
        # progress, but may cancel the workflow they requested.
        self.login(user=self.submitter)
        content = self.get_status(self.page).json()
        self.assertEqual(content["allowed_actions"], ["cancel"])

    def test_status_in_progress_editor_without_actions_sees_empty_list(self):
        # An editor who is neither the requester, the page owner, nor a
        # current task-group member passes the read gate but has no
        # available workflow actions.
        editor = self.create_user(username="plain-editor", password="password")
        group = Group.objects.create(name="Plain editors")
        editor.groups.add(group)
        GroupPagePermission.objects.create(
            group=group,
            page=Page.objects.get(depth=1),
            permission=Permission.objects.get(
                content_type__app_label=Page._meta.app_label,
                codename=Page.PERMISSION_CODENAMES.CHANGE,
            ),
        )
        self.submit_page()
        self.login(user=editor)
        response = self.get_status(self.page)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["allowed_actions"], [])

    def test_status_fresh_page(self):
        # No workflow has been started: there is no state yet and the editor
        # may submit. The assigned (but not started) workflow is reported.
        self.login(user=self.submitter)
        response = self.get_status(self.page)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["workflow"]["name"], "test_workflow")
        self.assertIsNone(content["workflow_state"])
        self.assertEqual(content["allowed_actions"], ["submit"])

    def test_status_fresh_page_denied_without_edit_permission(self):
        # A user without page edit permission and with no active workflow has
        # no read-gate branch that admits them: task actions only exist once
        # the workflow is in progress.
        self.login(user=self.bare_approver)
        self.assert_problem_response(self.get_status(self.page), status_code=403)
        self.login(user=self.outsider)
        self.assert_problem_response(self.get_status(self.page), status_code=403)

    def test_status_after_cancel_shows_cancelled_state_and_submit(self):
        self.submit_page()
        self.login(user=self.submitter)
        self.assertEqual(self.post_workflow("cancel", self.page).status_code, 200)
        response = self.get_status(self.page)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["workflow_state"]["status"], "cancelled")
        # No active state and the submitter can edit, so submit is available
        # again.
        self.assertEqual(content["allowed_actions"], ["submit"])

    @override_settings(WAGTAIL_WORKFLOW_ENABLED=False)
    def test_status_workflow_disabled_reports_nulls(self):
        self.login(user=self.submitter)
        response = self.get_status(self.page)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertIsNone(content["workflow"])
        self.assertIsNone(content["workflow_state"])
        self.assertEqual(content["allowed_actions"], [])

    # Read gate

    def test_status_read_gate_matrix(self):
        # Editors pass, the current task's group members pass, everyone else
        # gets 403, anonymous gets 401.
        self.submit_page()
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
                response = self.get_status(self.page)
                self.assertEqual(response.status_code, expected_status)
                if expected_status == 200:
                    self.assertEqual(
                        response.json()["workflow_state"]["status"], "in_progress"
                    )

    def test_status_unknown_page_returns_404(self):
        self.login(user=self.submitter)
        last_id = Page.objects.order_by("-id").values_list("id", flat=True).first()
        assert last_id is not None
        response = self.client.get(
            reverse("wagtailapi_v3:get_page_workflow", kwargs={"page_id": last_id + 1})
        )
        self.assert_problem_response(response, status_code=404)


class TestPageWorkflowHistory(WorkflowReadsMixin, TestV3WorkflowBase, TestCase):
    def setUp(self):
        super().setUp()
        self.outsider = self.create_user(username="outsider", password="password")

    def submit_and_cancel(self):
        self.login(user=self.submitter)
        self.assertEqual(self.post_workflow("submit", self.page).status_code, 200)
        self.assertEqual(self.post_workflow("cancel", self.page).status_code, 200)

    def test_history_on_fresh_page_is_empty(self):
        self.login(user=self.submitter)
        response = self.get_history(self.page)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"count": 0, "items": []})

    def test_history_pagination_newest_first_and_scope(self):
        self.submit_and_cancel()
        # Cancel the second run too, so the page ends with two states: the
        # newest in progress (cancelled second) is listed first.
        self.submit_and_cancel()
        response = self.get_history(self.page)
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
        # Only this page's states are returned.
        self.assertEqual(
            set(ids),
            set(self.page.workflow_states.values_list("id", flat=True)),
        )

        # Limit/offset pagination honours the envelope.
        content = self.get_history(self.page, {"limit": 1}).json()
        self.assertEqual(content["count"], 2)
        self.assertEqual(len(content["items"]), 1)
        self.assertEqual(content["items"][0]["id"], ids[0])

    def test_history_items_are_lean(self):
        self.submit_and_cancel()
        self.login(user=self.submitter)
        items = self.get_history(self.page).json()["items"]
        for item in items:
            # Each item carries the task states it aggregates, but not the
            # workflow's full task timeline (that lives on the status
            # endpoint only).
            self.assertIn("task_states", item)
            self.assertNotIn("tasks", item)

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
                response = self.get_history(self.page)
                self.assertEqual(response.status_code, expected_status)

    def test_history_unknown_page_returns_404(self):
        self.login(user=self.submitter)
        last_id = Page.objects.order_by("-id").values_list("id", flat=True).first()
        assert last_id is not None
        response = self.client.get(
            reverse(
                "wagtailapi_v3:list_page_workflow_history",
                kwargs={"page_id": last_id + 1},
            )
        )
        self.assert_problem_response(response, status_code=404)
