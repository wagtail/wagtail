import datetime
import pytz

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.utils import IntegrityError
from django.test import TestCase

from wagtail.core.models import GroupApprovalTask, Page, Task, Workflow, WorkflowPage, WorkflowTask
from wagtail.tests.testapp.models import SimplePage

from freezegun import freeze_time


class TestWorkflows(TestCase):
    fixtures = ['test.json']

    def create_workflow_and_tasks(self):
        workflow = Workflow.objects.create(name='test_workflow')
        task_1 = Task.objects.create(name='test_task_1')
        task_2 = Task.objects.create(name='test_task_2')
        workflow_task_1 = WorkflowTask.objects.create(workflow=workflow, task=task_1, sort_order=1)
        workflow_task_2 = WorkflowTask.objects.create(workflow=workflow, task=task_2, sort_order=2)
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
        workflow_task = WorkflowTask.objects.create(workflow=workflow, task=task, sort_order=1)
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
        group_approval_task = GroupApprovalTask.objects.create(name='test_group_approval', group=Group.objects.first())
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

    def test_error_when_starting_multiple_in_progress_workflows(self):
        # test trying to start multiple status='in_progress' workflows on a single page will trigger an IntegrityError
        self.start_workflow_on_homepage()
        with self.assertRaises(IntegrityError):
            self.start_workflow_on_homepage()

    @freeze_time("2017-01-01 12:00:00")
    def test_approve_workflow(self):
        # tests that approving both TaskStates in a Workflow via Task.on_action approves tasks and publishes the revision correctly
        data = self.start_workflow_on_homepage()
        workflow_state = data['workflow_state']
        task_2 = data['task_2']
        page = data['page']
        task_state = workflow_state.current_task_state
        task_state.task.on_action(workflow_state, task_state, 'approve')
        self.assertEqual(task_state.finished_at, datetime.datetime(2017, 1, 1, 12, 0, 0, tzinfo=pytz.utc))
        self.assertEqual(task_state.status, 'approved')
        self.assertEqual(workflow_state.current_task_state.task, task_2)
        task_2.on_action(workflow_state, workflow_state.current_task_state, 'approve')
        self.assertEqual(workflow_state.status, 'approved')
        page.refresh_from_db()
        self.assertEqual(page.live_revision, workflow_state.current_task_state.page_revision)

    def test_workflow_resets_when_new_revision_created(self):
        # test that a Workflow on its second Task returns to its first task (upon WorkflowState.update()) if a new revision is created
        data = self.start_workflow_on_homepage()
        workflow_state = data['workflow_state']
        task_1 = data['task_1']
        task_2 = data['task_2']
        page = data['page']
        task_state = workflow_state.current_task_state
        task_state.task.on_action(workflow_state, task_state, 'approve')
        self.assertEqual(workflow_state.current_task_state.task, task_2)
        page.save_revision()
        workflow_state.update()
        task_state = workflow_state.current_task_state
        self.assertEqual(task_state.task, task_1)

    def test_reject_workflow(self):
        # test that both WorkflowState and TaskState are marked as rejected upon Task.on_action with action=reject
        data = self.start_workflow_on_homepage()
        workflow_state = data['workflow_state']
        task_1 = data['task_1']
        task_2 = data['task_2']
        page = data['page']
        task_state = workflow_state.current_task_state
        task_state.task.on_action(workflow_state, task_state, 'reject')
        self.assertEqual(task_state.status, 'rejected')
        self.assertEqual(workflow_state.status, 'rejected')



