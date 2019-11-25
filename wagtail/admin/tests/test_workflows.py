from django.test import TestCase
from django.urls import reverse

from wagtail.core.models import GroupApprovalTask, Page, Task, Workflow, WorkflowPage, WorkflowTask
from wagtail.tests.testapp.models import SimpleTask
from wagtail.tests.utils import WagtailTestUtils


class TestWorkflowsIndexView(TestCase, WagtailTestUtils):

    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_workflows:index'), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/workflows/index.html')

        # Initially there should be no workflows listed
        self.assertContains(response, "No workflows have been created.")

        Workflow.objects.create(name="test_workflow", active=True)

        # Now the listing should contain our workflow
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/workflows/index.html')
        self.assertNotContains(response, "No workflows have been created.")
        self.assertContains(response, "test_workflow")

    def test_deactivated(self):
        Workflow.objects.create(name="test_workflow", active=False)

        # The listing should contain our workflow, as well as marking it as disabled
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "No workflows have been created.")
        self.assertContains(response, "test_workflow")
        self.assertContains(response, "disabled")


class TestWorkflowsCreateView(TestCase, WagtailTestUtils):

    def setUp(self):
        self.login()
        self.task_1 = SimpleTask.objects.create(name="first_task")
        self.task_2 = SimpleTask.objects.create(name="second_task")


    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_workflows:add'), params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailadmin_workflows:add'), post_data)

    def test_get(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/workflows/create.html')

    def test_post(self):
        response = self.post({
            'name': ['test_workflow'], 'active': ['on'], 'workflow_tasks-TOTAL_FORMS': ['2'],
            'workflow_tasks-INITIAL_FORMS': ['0'], 'workflow_tasks-MIN_NUM_FORMS': ['0'],
            'workflow_tasks-MAX_NUM_FORMS': ['1000'], 'workflow_tasks-0-task': [str(self.task_1.id)], 'workflow_tasks-0-id': [''],
            'workflow_tasks-0-ORDER': ['1'], 'workflow_tasks-0-DELETE': [''], 'workflow_tasks-1-task': [str(self.task_2.id)],
            'workflow_tasks-1-id': [''], 'workflow_tasks-1-ORDER': ['2'], 'workflow_tasks-1-DELETE': ['']})


        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailadmin_workflows:index'))

        # Check that the workflow was created
        workflows = Workflow.objects.filter(name="test_workflow", active=True)
        self.assertEqual(workflows.count(), 1)

        workflow = workflows.first()

        # Check that the tasks are associated with the workflow
        self.assertEqual([self.task_1.task_ptr, self.task_2.task_ptr], list(workflow.tasks))

        # Check that the tasks have sort_order set on WorkflowTask correctly
        self.assertEqual(WorkflowTask.objects.get(workflow=workflow, task=self.task_1.task_ptr).sort_order, 0)
        self.assertEqual(WorkflowTask.objects.get(workflow=workflow, task=self.task_2.task_ptr).sort_order, 1)


class TestWorkflowsEditView(TestCase, WagtailTestUtils):

    def setUp(self):
        self.login()
        self.workflow = Workflow.objects.create(name="workflow_to_edit")
        self.task_1 = SimpleTask.objects.create(name="first_task")
        self.task_2 = SimpleTask.objects.create(name="second_task")
        self.inactive_task = SimpleTask.objects.create(name="inactive_task", active=False)
        self.workflow_task = WorkflowTask.objects.create(workflow=self.workflow, task=self.task_1.task_ptr, sort_order=0)
        self.page = Page.objects.first()
        WorkflowPage.objects.create(workflow=self.workflow, page=self.page)


    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_workflows:edit', args=[self.workflow.id]), params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailadmin_workflows:edit', args=[self.workflow.id]), post_data)

    def test_get(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/workflows/edit.html')

        # Test that the form contains options for the active tasks, but not the inactive task
        self.assertContains(response, "first_task")
        self.assertContains(response, "second_task")
        self.assertNotContains(response, "inactive_task")

        # Check that the list of pages has the page to which this workflow is assigned
        self.assertContains(response, self.page.title)

    def test_post(self):
        response = self.post({
            'name': [str(self.workflow.name)],
            'active': ['on'],
            'workflow_tasks-TOTAL_FORMS': ['2'],
            'workflow_tasks-INITIAL_FORMS': ['1'],
            'workflow_tasks-MIN_NUM_FORMS': ['0'],
            'workflow_tasks-MAX_NUM_FORMS': ['1000'],
            'workflow_tasks-0-task': [str(self.task_1.id)],
            'workflow_tasks-0-id': [str(self.workflow_task.id)],
            'workflow_tasks-0-ORDER': ['1'],
            'workflow_tasks-0-DELETE': [''],
            'workflow_tasks-1-task': [str(self.task_2.id)],
            'workflow_tasks-1-id': [''],
            'workflow_tasks-1-ORDER': ['2'],
            'workflow_tasks-1-DELETE': ['']})


        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailadmin_workflows:index'))

        # Check that the workflow was created
        workflows = Workflow.objects.filter(name="workflow_to_edit", active=True)
        self.assertEqual(workflows.count(), 1)

        workflow = workflows.first()

        # Check that the tasks are associated with the workflow
        self.assertEqual([self.task_1.task_ptr, self.task_2.task_ptr], list(workflow.tasks))

        # Check that the tasks have sort_order set on WorkflowTask correctly
        self.assertEqual(WorkflowTask.objects.get(workflow=workflow, task=self.task_1.task_ptr).sort_order, 0)
        self.assertEqual(WorkflowTask.objects.get(workflow=workflow, task=self.task_2.task_ptr).sort_order, 1)


class TestAddWorkflowToPage(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.login()
        self.workflow = Workflow.objects.create(name="workflow")
        self.page = Page.objects.first()
        self.other_workflow = Workflow.objects.create(name="other_workflow")
        self.other_page = Page.objects.last()
        WorkflowPage.objects.create(workflow=self.other_workflow, page=self.other_page)

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_workflows:add_to_page', args=[self.workflow.id]), params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailadmin_workflows:add_to_page', args=[self.workflow.id]), post_data)

    def test_get(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/workflows/add_to_page.html')

    def test_post(self):
        # Check that a WorkflowPage instance is created correctly when a page with no existing workflow is created
        response = self.post({'page': str(self.page.id), 'workflow': str(self.workflow.id)})
        self.assertEqual(WorkflowPage.objects.filter(workflow=self.workflow, page=self.page).count(), 1)

        # Check that trying to add a WorkflowPage for a page with an existing workflow does not create
        response = self.post({'page': str(self.other_page.id), 'workflow': str(self.workflow.id)})
        self.assertEqual(WorkflowPage.objects.filter(workflow=self.workflow, page=self.other_page).count(), 0)

        # Check that this can be overridden by setting overwrite_existing to true
        response = self.post({'page': str(self.other_page.id), 'overwrite_existing': 'True', 'workflow': str(self.workflow.id)})
        self.assertEqual(WorkflowPage.objects.filter(workflow=self.workflow, page=self.other_page).count(), 1)


class TestRemoveWorkflow(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.login()
        self.workflow = Workflow.objects.create(name="workflow")
        self.page = Page.objects.first()
        WorkflowPage.objects.create(workflow=self.workflow, page=self.page)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailadmin_workflows:remove', args=[self.workflow.id, self.page.id]), post_data)

    def test_post(self):
        # Check that a WorkflowPage instance is removed correctly
        response = self.post()
        self.assertEqual(WorkflowPage.objects.filter(workflow=self.workflow, page=self.page).count(), 0)


class TestTaskIndexView(TestCase, WagtailTestUtils):

    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_workflows:task_index'), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/workflows/task_index.html')

        # Initially there should be no tasks listed
        self.assertContains(response, "No tasks have been created.")

        SimpleTask.objects.create(name="test_task", active=True)

        # Now the listing should contain our task
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/workflows/task_index.html')
        self.assertNotContains(response, "No tasks have been created.")
        self.assertContains(response, "test_task")

    def test_deactivated(self):
        Task.objects.create(name="test_task", active=False)

        # The listing should contain our workflow, as well as marking it as disabled
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "No tasks have been created.")
        self.assertContains(response, "test_task")
        self.assertContains(response, "disabled")


class TestCreateTaskView(TestCase, WagtailTestUtils):

    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_workflows:add_task', kwargs={'app_label': SimpleTask._meta.app_label, 'model_name': SimpleTask._meta.model_name}), params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailadmin_workflows:add_task', kwargs={'app_label': SimpleTask._meta.app_label, 'model_name': SimpleTask._meta.model_name}), post_data)

    def test_get(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/workflows/create_task.html')

    def test_post(self):
        response = self.post({'name': 'test_task', 'active': 'on'})

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailadmin_workflows:task_index'))

        # Check that the task was created
        tasks = Task.objects.filter(name="test_task", active=True)
        self.assertEqual(tasks.count(), 1)


class TestSelectTaskTypeView(TestCase, WagtailTestUtils):

    def setUp(self):
        self.login()

    def get(self):
        return self.client.get(reverse('wagtailadmin_workflows:select_task_type'))

    def test_get(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/workflows/select_task_type.html')

        # Check that the list of available task types includes SimpleTask and GroupApprovalTask
        self.assertContains(response, SimpleTask.get_verbose_name())
        self.assertContains(response, GroupApprovalTask.get_verbose_name())


class TestEditTaskView(TestCase, WagtailTestUtils):

    def setUp(self):
        self.login()
        self.task = SimpleTask.objects.create(name="test_task")

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_workflows:edit_task', args=[self.task.id]), params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailadmin_workflows:edit_task', args=[self.task.id]), post_data)

    def test_get(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/workflows/edit_task.html')

    def test_post(self):
        response = self.post({'name': 'test_task_modified', 'active': 'on'})

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailadmin_workflows:task_index'))

        # Check that the task was updated
        task = Task.objects.get(id=self.task.id)
        self.assertEqual(task.name, "test_task_modified")
