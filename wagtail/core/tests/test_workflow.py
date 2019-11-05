from django.test import TestCase

from wagtail.core.models import Task, Workflow, WorkflowTask


class TestPageQuerySet(TestCase):
    fixtures = ['test.json']

    def test_create_workflow(self):
        # test creating and retrieving an empty workflow from the db
        test_workflow = Workflow(name='test_workflow')
        test_workflow.save()
        retrieved_workflow = Workflow.objects.get(id=test_workflow.id)
        self.assertEqual(retrieved_workflow.name, 'test_workflow')

    def test_create_task(self):
        # test creating and retrieving a base task from the db
        test_task = Task(name='test_task')
        test_task.save()
        retrieved_task = Task.objects.get(id=test_task.id)
        self.assertEqual(retrieved_task.name, 'test_task')

    def test_add_task_to_workflow(self):
        workflow = Workflow.objects.create(name='test_workflow')
        task = Task.objects.create(name='test_task')
        workflow_task = WorkflowTask.objects.create(workflow=workflow, task=task, sort_order=1)
        self.assertIn(task, workflow.tasks.all())
        self.assertIn(workflow, task.workflows.all())
