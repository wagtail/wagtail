from django.contrib.auth.models import Group

from django.test import TestCase

from wagtail.core.models import GroupApprovalTask, Page, Task, Workflow, WorkflowTask

from wagtail.tests.testapp.models import (
    AbstractPage, Advert, AlwaysShowInMenusPage, BlogCategory, BlogCategoryBlogPage, BusinessChild,
    BusinessIndex, BusinessNowherePage, BusinessSubIndex, CustomManager, CustomManagerPage,
    CustomPageQuerySet, EventCategory, EventIndex, EventPage, GenericSnippetPage, ManyToManyBlogPage,
    MTIBasePage, MTIChildPage, MyCustomPage, OneToOnePage, PageWithExcludedCopyField, SimpleChildPage,
    SimplePage, SimpleParentPage, SingleEventPage, SingletonPage, StandardIndex, TaggedPage)

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

    def test_add_workflow_to_page(self):
        workflow = Workflow.objects.create(name='test_workflow')
        homepage = Page.objects.get(url_path='/home/')
        homepage.workflow = workflow
        homepage.save()
        homepage.refresh_from_db()
        self.assertEqual(homepage.workflow, workflow)

    def test_get_specific_task(self):
        group_approval_task = GroupApprovalTask.objects.create(name='test_group_approval', group=Group.objects.first())
        task = Task.objects.get(name='test_group_approval')
        specific_task = task.specific
        self.assertIsInstance(specific_task, GroupApprovalTask)

    def test_get_workflow_from_parent(self):
        workflow = Workflow.objects.create(name='test_workflow')
        homepage = Page.objects.get(url_path='/home/')
        homepage.workflow = workflow
        homepage.save()
        hello_page = SimplePage(title="Hello world", slug='hello-world', content="hello")
        homepage.add_child(instance=hello_page)
        self.assertEqual(hello_page.get_workflow(), workflow)

    def test_get_workflow_from_closest_ancestor(self):
        workflow_1 = Workflow.objects.create(name='test_workflow_1')
        workflow_2 = Workflow.objects.create(name='test_workflow_1')
        homepage = Page.objects.get(url_path='/home/')
        homepage.workflow = workflow_1
        homepage.save()
        hello_page = SimplePage(title="Hello world", slug='hello-world', content="hello", workflow=workflow_2)
        homepage.add_child(instance=hello_page)
        goodbye_page = SimplePage(title="Goodbye world", slug='goodbye-world', content="goodbye")
        hello_page.add_child(instance=goodbye_page)
        self.assertEqual(hello_page.get_workflow(), workflow_2)
        self.assertEqual(goodbye_page.get_workflow(), workflow_2)
