import datetime

import pytz
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase, override_settings

from freezegun import freeze_time
from wagtail.core.models import (
    GroupApprovalTask, Page, Task, TaskState, Workflow, WorkflowPage, WorkflowState, WorkflowTask)

from wagtail.tests.testapp.models import SimplePage


class TestWorkflows(TestCase):
    fixtures = ['test.json']

    def create_workflow_and_tasks(self):
        workflow = Workflow.objects.create(name='test_workflow')
        task_1 = Task.objects.create(name='test_task_1')
        task_2 = Task.objects.create(name='test_task_2')
        WorkflowTask.objects.create(workflow=workflow, task=task_1, sort_order=1)
        WorkflowTask.objects.create(workflow=workflow, task=task_2, sort_order=2)
        return workflow, task_1, task_2

    def start_workflow_on_homepage(self):
        workflow, task_1, task_2 = self.create_workflow_and_tasks()
        homepage = Page.objects.get(url_path='/home/')
        homepage.save_revision()
        user = get_user_model().objects.first()
        workflow_state = workflow.start(homepage, user)
        return {'workflow_state': workflow_state, 'user': user, 'page': homepage, 'task_1': task_1, 'task_2': task_2, 'workflow': workflow}

    def test_create_workflow(self):
        # test creating and retrieving an empty Workflow from the db
        test_workflow = Workflow(name='test_workflow')
        test_workflow.save()
        retrieved_workflow = Workflow.objects.get(id=test_workflow.id)
        self.assertEqual(retrieved_workflow.name, 'test_workflow')

    def test_create_task(self):
        # test creating and retrieving a base Task from the db
        test_task = Task(name='test_task')
        test_task.save()
        retrieved_task = Task.objects.get(id=test_task.id)
        self.assertEqual(retrieved_task.name, 'test_task')

    def test_add_task_to_workflow(self):
        workflow = Workflow.objects.create(name='test_workflow')
        task = Task.objects.create(name='test_task')
        WorkflowTask.objects.create(workflow=workflow, task=task, sort_order=1)
        self.assertIn(task, Task.objects.filter(workflow_tasks__workflow=workflow))
        self.assertIn(workflow, Workflow.objects.filter(workflow_tasks__task=task))

    def test_add_workflow_to_page(self):
        # test adding a Workflow to a Page via WorkflowPage
        workflow = Workflow.objects.create(name='test_workflow')
        homepage = Page.objects.get(url_path='/home/')
        WorkflowPage.objects.create(page=homepage, workflow=workflow)
        homepage.refresh_from_db()
        self.assertEqual(homepage.workflowpage.workflow, workflow)

    def test_get_specific_task(self):
        # test ability to get instance of subclassed Task type using Task.specific
        group_approval_task = GroupApprovalTask.objects.create(name='test_group_approval')
        group_approval_task.groups.set(Group.objects.all())
        task = Task.objects.get(name='test_group_approval')
        specific_task = task.specific
        self.assertIsInstance(specific_task, GroupApprovalTask)

    def test_get_workflow_from_parent(self):
        # test ability to use Page.get_workflow() to retrieve a Workflow from a parent Page if none is set directly
        workflow = Workflow.objects.create(name='test_workflow')
        homepage = Page.objects.get(url_path='/home/')
        WorkflowPage.objects.create(page=homepage, workflow=workflow)
        hello_page = SimplePage(title="Hello world", slug='hello-world', content="hello")
        homepage.add_child(instance=hello_page)
        self.assertEqual(hello_page.get_workflow(), workflow)
        self.assertTrue(workflow.all_pages().filter(id=hello_page.id).exists())

    def test_get_workflow_from_closest_ancestor(self):
        # test that using Page.get_workflow() tries to get the workflow from itself, then the closest ancestor, and does
        # not get Workflows from further up the page tree first
        workflow_1 = Workflow.objects.create(name='test_workflow_1')
        workflow_2 = Workflow.objects.create(name='test_workflow_2')
        homepage = Page.objects.get(url_path='/home/')
        WorkflowPage.objects.create(page=homepage, workflow=workflow_1)
        hello_page = SimplePage(title="Hello world", slug='hello-world', content="hello")
        homepage.add_child(instance=hello_page)
        WorkflowPage.objects.create(page=hello_page, workflow=workflow_2)
        goodbye_page = SimplePage(title="Goodbye world", slug='goodbye-world', content="goodbye")
        hello_page.add_child(instance=goodbye_page)
        self.assertEqual(hello_page.get_workflow(), workflow_2)
        self.assertEqual(goodbye_page.get_workflow(), workflow_2)

        # Check the .all_pages() method
        self.assertFalse(workflow_1.all_pages().filter(id=hello_page.id).exists())
        self.assertFalse(workflow_1.all_pages().filter(id=goodbye_page.id).exists())
        self.assertTrue(workflow_2.all_pages().filter(id=hello_page.id).exists())
        self.assertTrue(workflow_2.all_pages().filter(id=goodbye_page.id).exists())

    @freeze_time("2017-01-01 12:00:00")
    def test_start_workflow_on_page(self):
        # test the first WorkflowState and TaskState models are set up correctly when Workflow.start(page) is used.
        workflow, task_1, task_2 = self.create_workflow_and_tasks()
        homepage = Page.objects.get(url_path='/home/')
        homepage.save_revision()
        user = get_user_model().objects.first()
        workflow_state = workflow.start(homepage, user)
        self.assertEqual(workflow_state.workflow, workflow)
        self.assertEqual(workflow_state.page, homepage)
        self.assertEqual(workflow_state.status, 'in_progress')
        self.assertEqual(workflow_state.created_at, datetime.datetime(2017, 1, 1, 12, 0, 0, tzinfo=pytz.utc))
        self.assertEqual(workflow_state.requested_by, user)

        task_state = workflow_state.current_task_state
        self.assertEqual(task_state.task, task_1)
        self.assertEqual(task_state.status, 'in_progress')
        self.assertEqual(task_state.page_revision, homepage.get_latest_revision())
        self.assertEqual(task_state.started_at, datetime.datetime(2017, 1, 1, 12, 0, 0, tzinfo=pytz.utc))
        self.assertEqual(task_state.finished_at, None)

    @override_settings(WAGTAIL_WORKFLOW_CANCEL_ON_PUBLISH=True)
    def test_publishing_page_cancels_workflow_when_cancel_on_publish_true(self):
        data = self.start_workflow_on_homepage()
        data['page'].get_latest_revision().publish()
        workflow_state = data['workflow_state']
        workflow_state.refresh_from_db()
        self.assertEqual(workflow_state.status, WorkflowState.STATUS_CANCELLED)

    @override_settings(WAGTAIL_WORKFLOW_CANCEL_ON_PUBLISH=False)
    def test_publishing_page_does_not_cancel_workflow_when_cancel_on_publish_false(self):
        data = self.start_workflow_on_homepage()
        data['page'].get_latest_revision().publish()
        workflow_state = data['workflow_state']
        workflow_state.refresh_from_db()
        self.assertEqual(workflow_state.status, WorkflowState.STATUS_IN_PROGRESS)

    def test_error_when_starting_multiple_in_progress_workflows(self):
        # test trying to start multiple status='in_progress' workflows on a single page will trigger an IntegrityError
        self.start_workflow_on_homepage()
        with self.assertRaises((IntegrityError, ValidationError)):
            self.start_workflow_on_homepage()

    @freeze_time("2017-01-01 12:00:00")
    def test_approve_workflow(self):
        # tests that approving both TaskStates in a Workflow via Task.on_action approves tasks and publishes the revision correctly
        data = self.start_workflow_on_homepage()
        workflow_state = data['workflow_state']
        task_2 = data['task_2']
        page = data['page']
        task_state = workflow_state.current_task_state
        task_state.task.on_action(task_state, user=None, action_name='approve')
        self.assertEqual(task_state.finished_at, datetime.datetime(2017, 1, 1, 12, 0, 0, tzinfo=pytz.utc))
        self.assertEqual(task_state.status, 'approved')
        self.assertEqual(workflow_state.current_task_state.task, task_2)
        task_2.on_action(workflow_state.current_task_state, user=None, action_name='approve')
        self.assertEqual(workflow_state.status, 'approved')
        page.refresh_from_db()
        self.assertEqual(page.live_revision, workflow_state.current_task_state.page_revision)

    @override_settings(WAGTAIL_WORKFLOW_REQUIRE_REAPPROVAL_ON_EDIT=True)
    def test_workflow_resets_when_new_revision_created(self):
        # test that a Workflow on its second Task returns to its first task (upon WorkflowState.update()) if a new revision is created
        data = self.start_workflow_on_homepage()
        workflow_state = data['workflow_state']
        task_1 = data['task_1']
        task_2 = data['task_2']
        page = data['page']
        task_state = workflow_state.current_task_state
        task_state.task.on_action(task_state, user=None, action_name='approve')
        self.assertEqual(workflow_state.current_task_state.task, task_2)
        page.save_revision()
        workflow_state.refresh_from_db()
        task_state = workflow_state.current_task_state
        task_state.task.on_action(task_state, user=None, action_name='approve')
        workflow_state.refresh_from_db()
        task_state = workflow_state.current_task_state
        self.assertEqual(task_state.task, task_1)

    @override_settings(WAGTAIL_WORKFLOW_REQUIRE_REAPPROVAL_ON_EDIT=False)
    def test_workflow_does_not_reset_when_new_revision_created_if_reapproval_turned_off(self):
        # test that a Workflow on its second Task does not return to its first task (upon approval) if a new revision is created
        data = self.start_workflow_on_homepage()
        workflow_state = data['workflow_state']
        task_1 = data['task_1']
        task_2 = data['task_2']
        page = data['page']
        task_state = workflow_state.current_task_state
        task_state.task.on_action(task_state, user=None, action_name='approve')
        self.assertEqual(workflow_state.current_task_state.task, task_2)
        page.save_revision()
        workflow_state.refresh_from_db()
        task_state = workflow_state.current_task_state
        task_state.task.on_action(task_state, user=None, action_name='approve')
        workflow_state.refresh_from_db()
        task_state = workflow_state.current_task_state
        self.assertNotEqual(task_state.task, task_1)
        self.assertEqual(workflow_state.status, workflow_state.STATUS_APPROVED)

    def test_reject_workflow(self):
        # test that TaskState is marked as rejected upon Task.on_action with action=reject
        # and the WorkflowState as needs changes
        data = self.start_workflow_on_homepage()
        workflow_state = data['workflow_state']
        task_state = workflow_state.current_task_state
        task_state.task.on_action(task_state, user=None, action_name='reject')
        self.assertEqual(task_state.status, task_state.STATUS_REJECTED)
        self.assertEqual(workflow_state.status, workflow_state.STATUS_NEEDS_CHANGES)

    def test_resume_workflow(self):
        # test that a Workflow rejected on its second Task can be resumed on the second task
        data = self.start_workflow_on_homepage()
        workflow_state = data['workflow_state']
        task_2 = data['task_2']
        workflow_state.current_task_state.approve(user=None)
        workflow_state.refresh_from_db()
        workflow_state.current_task_state.reject(user=None)
        workflow_state.refresh_from_db()
        workflow_state.resume(user=None)

        self.assertEqual(workflow_state.status, workflow_state.STATUS_IN_PROGRESS)
        self.assertEqual(workflow_state.current_task_state.status, workflow_state.current_task_state.STATUS_IN_PROGRESS)
        self.assertEqual(workflow_state.current_task_state.task, task_2)
        self.assertTrue(workflow_state.is_active)

    def test_tasks_with_status_on_resubmission(self):
        # test that a Workflow rejected and resumed shows the status of the latest tasks when _`all_tasks_with_status` is called
        data = self.start_workflow_on_homepage()
        workflow_state = data['workflow_state']

        tasks = workflow_state.all_tasks_with_status()
        self.assertEqual(tasks[0].status, TaskState.STATUS_IN_PROGRESS)
        self.assertEqual(tasks[1].status_display, 'Not started')

        workflow_state.current_task_state.approve(user=None)
        workflow_state.refresh_from_db()

        workflow_state.current_task_state.reject(user=None)
        workflow_state.refresh_from_db()

        tasks = workflow_state.all_tasks_with_status()
        self.assertEqual(tasks[0].status, TaskState.STATUS_APPROVED)
        self.assertEqual(tasks[1].status, TaskState.STATUS_REJECTED)

        workflow_state.resume(user=None)

        tasks = workflow_state.all_tasks_with_status()
        self.assertEqual(tasks[0].status, TaskState.STATUS_APPROVED)
        self.assertEqual(tasks[1].status, TaskState.STATUS_IN_PROGRESS)

    def cancel_workflow(self):
        # test that cancelling a workflow state sets both current task state and its own statuses to cancelled, and cancels all in progress states
        data = self.start_workflow_on_homepage()
        workflow_state = data['workflow_state']
        workflow_state.cancel(user=None)
        self.assertEqual(workflow_state.status, WorkflowState.STATUS_CANCELLED)
        self.assertEqual(workflow_state.current_task_state.status, TaskState.STATUS_CANCELLED)
        self.assertFalse(TaskState.objects.filter(workflow_state=workflow_state, status=TaskState.STATUS_IN_PROGRESS).exists())
        self.assertFalse(workflow_state.is_active)

    def test_task_workflows(self):
        workflow = Workflow.objects.create(name='test_workflow')
        disabled_workflow = Workflow.objects.create(name="disabled_workflow", active=False)
        task = Task.objects.create(name='test_task')

        WorkflowTask.objects.create(workflow=workflow, task=task, sort_order=1)
        WorkflowTask.objects.create(workflow=disabled_workflow, task=task, sort_order=1)

        self.assertEqual(
            list(task.workflows), [workflow, disabled_workflow]
        )
        self.assertEqual(
            list(task.active_workflows), [workflow]
        )

    def test_is_at_final_task(self):
        # test that a Workflow rejected on its second Task can be resumed on the second task
        data = self.start_workflow_on_homepage()
        workflow_state = data['workflow_state']

        self.assertFalse(workflow_state.is_at_final_task)
        workflow_state.current_task_state.approve(user=None)
        workflow_state.refresh_from_db()
        self.assertTrue(workflow_state.is_at_final_task)

    def test_tasks_with_state(self):
        data = self.start_workflow_on_homepage()
        workflow_state = data['workflow_state']

        tasks = workflow_state.all_tasks_with_state()
        self.assertEqual(tasks[0].task_state.status, TaskState.STATUS_IN_PROGRESS)

        workflow_state.current_task_state.approve(user=None)
        workflow_state.refresh_from_db()

        workflow_state.current_task_state.reject(user=None)
        workflow_state.refresh_from_db()

        tasks = workflow_state.all_tasks_with_state()
        self.assertEqual(tasks[0].task_state.status, TaskState.STATUS_APPROVED)
        self.assertEqual(tasks[1].task_state.status, TaskState.STATUS_REJECTED)

        workflow_state.resume(user=None)

        tasks = workflow_state.all_tasks_with_state()
        self.assertEqual(tasks[0].task_state.status, TaskState.STATUS_APPROVED)
        self.assertEqual(tasks[1].task_state.status, TaskState.STATUS_IN_PROGRESS)
        self.assertEqual(
            tasks[1].task_state,
            TaskState.objects.filter(workflow_state=workflow_state).order_by('-started_at', '-id')[0]
        )
