from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.utils import timezone

from wagtail.actions import (
    ResumePageWorkflowAction,
    ResumeWorkflowAction,
    SubmitPageWorkflowAction,
    SubmitWorkflowAction,
    WorkflowStateError,
)
from wagtail.actions.registry import action_registry
from wagtail.log_actions import registry as log_registry
from wagtail.models import (
    GroupApprovalTask,
    Task,
    TaskState,
    Workflow,
    WorkflowContentType,
    WorkflowPage,
    WorkflowState,
    WorkflowTask,
)
from wagtail.test.testapp.models import FullFeaturedSnippet, SimplePage
from wagtail.test.utils import Page, WagtailTestUtils


def delete_existing_workflows():
    WorkflowPage.objects.all().delete()
    Workflow.objects.all().delete()
    Task.objects.all().delete()
    WorkflowTask.objects.all().delete()


class BaseWorkflowActionTests(WagtailTestUtils, TestCase):
    def setUp(self):
        delete_existing_workflows()
        self.submitter = self.create_user(username="submitter", password="password")
        Group.objects.get(name="Editors").user_set.add(self.submitter)
        self.moderator = self.create_user(username="moderator", password="password")
        Group.objects.get(name="Moderators").user_set.add(self.moderator)
        self.bare_approver = self.create_user(
            username="bare-approver", password="password"
        )
        bare_approvers = Group.objects.create(name="Bare approvers")
        self.bare_approver.groups.add(bare_approvers)
        self.superuser = self.create_superuser(
            username="superuser", password="password"
        )

        self.workflow = Workflow.objects.create(name="test_workflow")
        self.task_1 = GroupApprovalTask.objects.create(name="test_task_1")
        self.task_2 = GroupApprovalTask.objects.create(name="test_task_2")
        for i, task in enumerate((self.task_1, self.task_2), start=1):
            task.groups.set(
                Group.objects.filter(name__in=["Moderators", "Bare approvers"])
            )
            WorkflowTask.objects.create(workflow=self.workflow, task=task, sort_order=i)

    def assert_log_actions(self, instance, actions, since=None):
        # Local copy of the assertion helper from
        # wagtail/api/v3/tests/base.py, so the action tests have no API
        # dependency.
        logs = log_registry.get_logs_for_instance(instance)
        if since:
            logs = logs.filter(timestamp__gte=since)
        new_actions = list(logs.order_by("timestamp").values_list("action", flat=True))
        self.assertEqual(new_actions, actions)


class BasePageWorkflowActionTests(BaseWorkflowActionTests):
    def setUp(self):
        super().setUp()

        self.object = SimplePage(
            title="Hello world!", slug="hello-world", content="hello", live=False
        )
        Page.objects.get(depth=2).add_child(instance=self.object)
        WorkflowPage.objects.create(workflow=self.workflow, page=self.object)
        self.object.save_revision(user=self.submitter)


class BaseSnippetWorkflowActionTests(BaseWorkflowActionTests):
    def setUp(self):
        super().setUp()

        self.object = FullFeaturedSnippet.objects.create(
            text="Hello world!", live=False
        )
        WorkflowContentType.objects.create(
            workflow=self.workflow,
            content_type=ContentType.objects.get_for_model(FullFeaturedSnippet),
        )
        self.object.save_revision(user=self.submitter)
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


class TestSubmitWorkflowAction(BasePageWorkflowActionTests):
    def test_submit_starts_workflow_and_logs(self):
        since = timezone.now()

        state = SubmitWorkflowAction(self.object, user=self.submitter).execute()

        self.assertEqual(state.status, WorkflowState.STATUS_IN_PROGRESS)
        self.assertEqual(state.current_task_state.task_id, self.task_1.id)
        self.assertEqual(state.current_task_state.status, TaskState.STATUS_IN_PROGRESS)
        self.assert_log_actions(self.object, ["wagtail.workflow.start"], since=since)

    def test_submit_creates_state_on_latest_revision(self):
        self.object.save_revision(user=self.submitter)

        state = SubmitWorkflowAction(self.object, user=self.submitter).execute()

        self.assertEqual(
            state.current_task_state.revision, self.object.get_latest_revision()
        )

    def test_submit_without_workflow_raises_state_error(self):
        WorkflowPage.objects.get(page=self.object).delete()
        # Clear the cached reverse relation (set when the WorkflowPage was
        # created against this instance), so get_workflow() re-queries.
        self.object.refresh_from_db()

        with self.assertRaises(WorkflowStateError) as cm:
            SubmitWorkflowAction(self.object, user=self.submitter).execute()

        self.assertEqual(
            str(cm.exception), "There is no active workflow assigned to this object."
        )

    def test_submit_with_active_state_raises_state_error(self):
        SubmitWorkflowAction(self.object, user=self.submitter).execute()

        # The moderator is used because the in-progress GroupApprovalTask
        # locks the page for the submitter (403, see test_submit_locked_page);
        # calling as a reviewer reaches the state check instead.
        with self.assertRaises(WorkflowStateError) as cm:
            SubmitWorkflowAction(self.object, user=self.moderator).execute()

        self.assertEqual(
            str(cm.exception), "A workflow is already active on this object."
        )

    def test_submit_with_needs_changes_raises_state_error(self):
        state = SubmitWorkflowAction(self.object, user=self.submitter).execute()
        self.task_1.specific.on_action(
            state.current_task_state, self.moderator, "reject"
        )

        with self.assertRaises(WorkflowStateError) as cm:
            SubmitWorkflowAction(self.object, user=self.submitter).execute()

        self.assertEqual(
            str(cm.exception), "A workflow is already active on this object."
        )

    def test_submit_without_edit_permission_raises(self):
        user = self.create_user(username="unrelated")

        with self.assertRaises(PermissionDenied):
            SubmitWorkflowAction(self.object, user=user).execute()

    def test_submit_locked_page_raises(self):
        self.object.locked = True
        self.object.locked_by = self.moderator
        self.object.save(update_fields=["locked", "locked_by"])

        with self.assertRaises(PermissionDenied):
            SubmitWorkflowAction(self.object, user=self.submitter).execute()

    def test_registry_resolves_page_subclass(self):
        self.assertIs(
            action_registry.get_action_class(SimplePage, "submit"),
            SubmitPageWorkflowAction,
        )


class TestSubmitWorkflowActionSnippet(BaseSnippetWorkflowActionTests):
    def test_submit_starts_workflow_and_logs(self):
        since = timezone.now()

        state = SubmitWorkflowAction(self.object, user=self.submitter).execute()

        self.assertEqual(state.status, WorkflowState.STATUS_IN_PROGRESS)
        self.assertEqual(state.current_task_state.task_id, self.task_1.id)
        self.assertEqual(state.current_task_state.status, TaskState.STATUS_IN_PROGRESS)
        self.assert_log_actions(self.object, ["wagtail.workflow.start"], since=since)

    def test_submit_without_change_permission_raises(self):
        user = self.create_user(username="noperms")

        with self.assertRaises(PermissionDenied):
            SubmitWorkflowAction(self.object, user=user).execute()

    def test_submit_with_needs_changes_raises_state_error(self):
        state = SubmitWorkflowAction(self.object, user=self.submitter).execute()
        self.task_1.specific.on_action(
            state.current_task_state, self.moderator, "reject"
        )

        with self.assertRaises(WorkflowStateError) as cm:
            SubmitWorkflowAction(self.object, user=self.submitter).execute()

        self.assertEqual(
            str(cm.exception), "A workflow is already active on this object."
        )


class TestResumeWorkflowAction(BasePageWorkflowActionTests):
    def test_resume_from_needs_changes(self):
        state = SubmitWorkflowAction(self.object, user=self.submitter).execute()
        rejected_task_state = state.current_task_state
        self.task_1.specific.on_action(rejected_task_state, self.moderator, "reject")
        state.refresh_from_db()
        self.assertEqual(state.status, WorkflowState.STATUS_NEEDS_CHANGES)

        since = timezone.now()

        state = ResumeWorkflowAction(self.object, user=self.submitter).execute()

        self.assertEqual(state.status, WorkflowState.STATUS_IN_PROGRESS)
        self.assertEqual(state.current_task_state.task_id, self.task_1.id)
        self.assertEqual(state.current_task_state.status, TaskState.STATUS_IN_PROGRESS)
        # The task is restarted with a new task state, not the rejected one.
        self.assertNotEqual(state.current_task_state.id, rejected_task_state.id)
        self.assert_log_actions(self.object, ["wagtail.workflow.resume"], since=since)

    def test_resume_from_in_progress_raises_state_error(self):
        SubmitWorkflowAction(self.object, user=self.submitter).execute()

        # The moderator is used because the in-progress GroupApprovalTask
        # locks the page for the submitter (403); a reviewer reaches the
        # state check instead.
        with self.assertRaises(WorkflowStateError) as cm:
            ResumeWorkflowAction(self.object, user=self.moderator).execute()

        self.assertEqual(
            str(cm.exception), "The workflow on this object is not awaiting changes."
        )

    def test_resume_no_state_raises_state_error(self):
        with self.assertRaises(WorkflowStateError) as cm:
            ResumeWorkflowAction(self.object, user=self.submitter).execute()

        self.assertEqual(
            str(cm.exception), "The workflow on this object is not awaiting changes."
        )

    def test_resume_without_edit_permission_raises(self):
        state = SubmitWorkflowAction(self.object, user=self.submitter).execute()
        self.task_1.specific.on_action(
            state.current_task_state, self.moderator, "reject"
        )
        user = self.create_user(username="unrelated")

        with self.assertRaises(PermissionDenied):
            ResumeWorkflowAction(self.object, user=user).execute()

    def test_registry_resolves_page_subclass(self):
        self.assertIs(
            action_registry.get_action_class(SimplePage, "resume"),
            ResumePageWorkflowAction,
        )


class TestResumeWorkflowActionSnippet(BaseSnippetWorkflowActionTests):
    def test_resume_from_needs_changes(self):
        state = SubmitWorkflowAction(self.object, user=self.submitter).execute()
        self.task_1.specific.on_action(
            state.current_task_state, self.moderator, "reject"
        )

        since = timezone.now()

        state = ResumeWorkflowAction(self.object, user=self.submitter).execute()

        self.assertEqual(state.status, WorkflowState.STATUS_IN_PROGRESS)
        self.assertEqual(state.current_task_state.task_id, self.task_1.id)
        self.assert_log_actions(self.object, ["wagtail.workflow.resume"], since=since)

    def test_resume_no_state_raises_state_error(self):
        with self.assertRaises(WorkflowStateError) as cm:
            ResumeWorkflowAction(self.object, user=self.submitter).execute()

        self.assertEqual(
            str(cm.exception), "The workflow on this object is not awaiting changes."
        )
