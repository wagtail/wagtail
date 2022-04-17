import json
import logging
from unittest import mock

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.test import TestCase, override_settings
from django.urls import reverse
from freezegun import freeze_time

from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.models import (
    GroupApprovalTask,
    Page,
    Task,
    TaskState,
    Workflow,
    WorkflowPage,
    WorkflowState,
    WorkflowTask,
)
from wagtail.signals import page_published
from wagtail.test.testapp.models import SimplePage, SimpleTask
from wagtail.test.utils import WagtailTestUtils
from wagtail.users.models import UserProfile


def delete_existing_workflows():
    WorkflowPage.objects.all().delete()
    Workflow.objects.all().delete()
    Task.objects.all().delete()
    WorkflowTask.objects.all().delete()


class TestWorkflowMenus(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        self.editor = self.create_user(
            username="editor",
            email="editor@email.com",
            password="password",
        )
        editors = Group.objects.get(name="Editors")
        editors.user_set.add(self.editor)

    def test_workflow_settings_and_reports_menus_are_shown_to_admin(self):
        response = self.client.get("/admin/")
        self.assertContains(response, '"url": "/admin/workflows/list/"')
        self.assertContains(response, '"url": "/admin/workflows/tasks/index/"')
        self.assertContains(response, '"url": "/admin/reports/workflow/"')
        self.assertContains(response, '"url": "/admin/reports/workflow_tasks/"')

    def test_workflow_settings_menus_are_not_shown_to_editor(self):
        self.login(user=self.editor)
        response = self.client.get("/admin/")
        self.assertNotContains(response, '"url": "/admin/workflows/list/"')
        self.assertNotContains(response, '"url": "/admin/workflows/tasks/index/"')
        self.assertContains(response, '"url": "/admin/reports/workflow/"')
        self.assertContains(response, '"url": "/admin/reports/workflow_tasks/"')

    @override_settings(WAGTAIL_WORKFLOW_ENABLED=False)
    def test_workflow_menus_are_hidden_when_workflows_are_disabled(self):
        response = self.client.get("/admin/")
        self.assertNotContains(response, '"url": "/admin/workflows/list/"')
        self.assertNotContains(response, '"url": "/admin/workflows/tasks/index/"')
        self.assertNotContains(response, '"url": "/admin/reports/workflow/"')
        self.assertNotContains(response, '"url": "/admin/reports/workflow_tasks/"')


class TestWorkflowsIndexView(TestCase, WagtailTestUtils):
    def setUp(self):
        delete_existing_workflows()
        self.login()

        self.editor = self.create_user(
            username="editor",
            email="editor@email.com",
            password="password",
        )
        editors = Group.objects.get(name="Editors")
        editors.user_set.add(self.editor)

        self.moderator = self.create_user(
            username="moderator",
            email="moderator@email.com",
            password="password",
        )
        moderators = Group.objects.get(name="Moderators")
        moderators.user_set.add(self.moderator)
        moderators.permissions.add(Permission.objects.get(codename="add_workflow"))

    def get(self, params={}):
        return self.client.get(reverse("wagtailadmin_workflows:index"), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/workflows/index.html")

        # Initially there should be no workflows listed
        self.assertContains(response, "There are no enabled workflows.")

        Workflow.objects.create(name="test_workflow", active=True)

        # Now the listing should contain our workflow
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/workflows/index.html")
        self.assertNotContains(response, "There are no enabled workflows.")
        self.assertContains(response, "test_workflow")

    def test_deactivated(self):
        Workflow.objects.create(name="test_workflow", active=False)

        # The listing should contain our workflow, as well as marking it as disabled
        response = self.get(params={"show_disabled": "true"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "No workflows have been created.")
        self.assertContains(response, "test_workflow")
        self.assertContains(
            response, '<span class="status-tag">Disabled</span>', html=True
        )

        # If we set 'show_disabled' to 'False', the workflow should not be displayed
        response = self.get(params={})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "There are no enabled workflows.")

    def test_permissions(self):
        self.login(user=self.editor)
        response = self.get()
        self.assertEqual(response.status_code, 302)
        full_context = {
            key: value for context in response.context for key, value in context.items()
        }
        self.assertEqual(
            full_context["message"],
            "Sorry, you do not have permission to access this area.",
        )

        self.login(user=self.moderator)
        response = self.get()
        self.assertEqual(response.status_code, 200)


class TestWorkflowsCreateView(TestCase, WagtailTestUtils):
    def setUp(self):
        delete_existing_workflows()
        self.login()
        self.task_1 = SimpleTask.objects.create(name="first_task")
        self.task_2 = SimpleTask.objects.create(name="second_task")

        self.editor = self.create_user(
            username="editor",
            email="editor@email.com",
            password="password",
        )
        editors = Group.objects.get(name="Editors")
        editors.user_set.add(self.editor)

        self.moderator = self.create_user(
            username="moderator",
            email="moderator@email.com",
            password="password",
        )
        moderators = Group.objects.get(name="Moderators")
        moderators.user_set.add(self.moderator)
        moderators.permissions.add(Permission.objects.get(codename="add_workflow"))

        self.root_page = Page.objects.get(depth=1)

    def get(self, params={}):
        return self.client.get(reverse("wagtailadmin_workflows:add"), params)

    def post(self, post_data={}):
        return self.client.post(reverse("wagtailadmin_workflows:add"), post_data)

    def test_get(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/workflows/create.html")

    def test_post(self):
        response = self.post(
            {
                "name": ["test_workflow"],
                "active": ["on"],
                "workflow_tasks-TOTAL_FORMS": ["2"],
                "workflow_tasks-INITIAL_FORMS": ["0"],
                "workflow_tasks-MIN_NUM_FORMS": ["0"],
                "workflow_tasks-MAX_NUM_FORMS": ["1000"],
                "workflow_tasks-0-task": [str(self.task_1.id)],
                "workflow_tasks-0-id": [""],
                "workflow_tasks-0-ORDER": ["1"],
                "workflow_tasks-0-DELETE": [""],
                "workflow_tasks-1-task": [str(self.task_2.id)],
                "workflow_tasks-1-id": [""],
                "workflow_tasks-1-ORDER": ["2"],
                "workflow_tasks-1-DELETE": [""],
                "pages-TOTAL_FORMS": ["2"],
                "pages-INITIAL_FORMS": ["1"],
                "pages-MIN_NUM_FORMS": ["0"],
                "pages-MAX_NUM_FORMS": ["1000"],
                "pages-0-page": [str(self.root_page.id)],
                "pages-0-DELETE": [""],
                "pages-1-page": [""],
                "pages-1-DELETE": [""],
            }
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailadmin_workflows:index"))

        # Check that the workflow was created
        workflows = Workflow.objects.filter(name="test_workflow", active=True)
        self.assertEqual(workflows.count(), 1)

        workflow = workflows.first()

        # Check that the tasks are associated with the workflow
        self.assertEqual(
            [self.task_1.task_ptr, self.task_2.task_ptr], list(workflow.tasks)
        )

        # Check that the tasks have sort_order set on WorkflowTask correctly
        self.assertEqual(
            WorkflowTask.objects.get(
                workflow=workflow, task=self.task_1.task_ptr
            ).sort_order,
            0,
        )
        self.assertEqual(
            WorkflowTask.objects.get(
                workflow=workflow, task=self.task_2.task_ptr
            ).sort_order,
            1,
        )

    def test_permissions(self):
        self.login(user=self.editor)
        response = self.get()
        self.assertEqual(response.status_code, 302)
        full_context = {
            key: value for context in response.context for key, value in context.items()
        }
        self.assertEqual(
            full_context["message"],
            "Sorry, you do not have permission to access this area.",
        )

        self.login(user=self.moderator)
        response = self.get()
        self.assertEqual(response.status_code, 200)

    def test_page_already_has_workflow_check(self):
        workflow = Workflow.objects.create(name="existing_workflow")
        WorkflowPage.objects.create(workflow=workflow, page=self.root_page)

        response = self.post(
            {
                "name": ["test_workflow"],
                "active": ["on"],
                "workflow_tasks-TOTAL_FORMS": ["2"],
                "workflow_tasks-INITIAL_FORMS": ["0"],
                "workflow_tasks-MIN_NUM_FORMS": ["0"],
                "workflow_tasks-MAX_NUM_FORMS": ["1000"],
                "workflow_tasks-0-task": [str(self.task_1.id)],
                "workflow_tasks-0-id": [""],
                "workflow_tasks-0-ORDER": ["1"],
                "workflow_tasks-0-DELETE": [""],
                "workflow_tasks-1-task": [str(self.task_2.id)],
                "workflow_tasks-1-id": [""],
                "workflow_tasks-1-ORDER": ["2"],
                "workflow_tasks-1-DELETE": [""],
                "pages-TOTAL_FORMS": ["2"],
                "pages-INITIAL_FORMS": ["1"],
                "pages-MIN_NUM_FORMS": ["0"],
                "pages-MAX_NUM_FORMS": ["1000"],
                "pages-0-page": [str(self.root_page.id)],
                "pages-0-DELETE": [""],
                "pages-1-page": [""],
                "pages-1-DELETE": [""],
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormsetError(
            response,
            "pages_formset",
            0,
            "page",
            ["This page already has workflow 'existing_workflow' assigned."],
        )


class TestWorkflowsEditView(TestCase, WagtailTestUtils):
    def setUp(self):
        delete_existing_workflows()
        self.login()
        self.workflow = Workflow.objects.create(name="workflow_to_edit")
        self.task_1 = SimpleTask.objects.create(name="first_task")
        self.task_2 = SimpleTask.objects.create(name="second_task")
        self.inactive_task = SimpleTask.objects.create(
            name="inactive_task", active=False
        )
        self.workflow_task = WorkflowTask.objects.create(
            workflow=self.workflow, task=self.task_1.task_ptr, sort_order=0
        )
        self.page = Page.objects.first()
        WorkflowPage.objects.create(workflow=self.workflow, page=self.page)

        self.editor = self.create_user(
            username="editor",
            email="editor@email.com",
            password="password",
        )
        editors = Group.objects.get(name="Editors")
        editors.user_set.add(self.editor)

        self.moderator = self.create_user(
            username="moderator",
            email="moderator@email.com",
            password="password",
        )
        moderators = Group.objects.get(name="Moderators")
        moderators.user_set.add(self.moderator)
        moderators.permissions.add(Permission.objects.get(codename="change_workflow"))

    def get(self, params={}):
        return self.client.get(
            reverse("wagtailadmin_workflows:edit", args=[self.workflow.id]), params
        )

    def post(self, post_data={}):
        return self.client.post(
            reverse("wagtailadmin_workflows:edit", args=[self.workflow.id]), post_data
        )

    def test_get(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/workflows/edit.html")

        # Check that the list of pages has the page to which this workflow is assigned
        self.assertContains(response, self.page.title)

    def test_post(self):
        response = self.post(
            {
                "name": [str(self.workflow.name)],
                "active": ["on"],
                "workflow_tasks-TOTAL_FORMS": ["2"],
                "workflow_tasks-INITIAL_FORMS": ["1"],
                "workflow_tasks-MIN_NUM_FORMS": ["0"],
                "workflow_tasks-MAX_NUM_FORMS": ["1000"],
                "workflow_tasks-0-task": [str(self.task_1.id)],
                "workflow_tasks-0-id": [str(self.workflow_task.id)],
                "workflow_tasks-0-ORDER": ["1"],
                "workflow_tasks-0-DELETE": [""],
                "workflow_tasks-1-task": [str(self.task_2.id)],
                "workflow_tasks-1-id": [""],
                "workflow_tasks-1-ORDER": ["2"],
                "workflow_tasks-1-DELETE": [""],
                "pages-TOTAL_FORMS": ["2"],
                "pages-INITIAL_FORMS": ["1"],
                "pages-MIN_NUM_FORMS": ["0"],
                "pages-MAX_NUM_FORMS": ["1000"],
                "pages-0-page": [str(self.page.id)],
                "pages-0-DELETE": [""],
                "pages-1-page": [""],
                "pages-1-DELETE": [""],
            }
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailadmin_workflows:index"))

        # Check that the workflow was created
        workflows = Workflow.objects.filter(name="workflow_to_edit", active=True)
        self.assertEqual(workflows.count(), 1)

        workflow = workflows.first()

        # Check that the tasks are associated with the workflow
        self.assertEqual(
            [self.task_1.task_ptr, self.task_2.task_ptr], list(workflow.tasks)
        )

        # Check that the tasks have sort_order set on WorkflowTask correctly
        self.assertEqual(
            WorkflowTask.objects.get(
                workflow=workflow, task=self.task_1.task_ptr
            ).sort_order,
            0,
        )
        self.assertEqual(
            WorkflowTask.objects.get(
                workflow=workflow, task=self.task_2.task_ptr
            ).sort_order,
            1,
        )

    def test_permissions(self):
        self.login(user=self.editor)
        response = self.get()
        self.assertEqual(response.status_code, 302)
        full_context = {
            key: value for context in response.context for key, value in context.items()
        }
        self.assertEqual(
            full_context["message"],
            "Sorry, you do not have permission to access this area.",
        )

        self.login(user=self.moderator)
        response = self.get()
        self.assertEqual(response.status_code, 200)

    def test_admin_url_finder(self):
        editor_url_finder = AdminURLFinder(self.editor)
        self.assertIsNone(editor_url_finder.get_edit_url(self.workflow))
        moderator_url_finder = AdminURLFinder(self.moderator)
        expected_url = "/admin/workflows/edit/%d/" % self.workflow.pk
        self.assertEqual(moderator_url_finder.get_edit_url(self.workflow), expected_url)

    def test_duplicate_page_check(self):
        response = self.post(
            {
                "name": [str(self.workflow.name)],
                "active": ["on"],
                "workflow_tasks-TOTAL_FORMS": ["2"],
                "workflow_tasks-INITIAL_FORMS": ["1"],
                "workflow_tasks-MIN_NUM_FORMS": ["0"],
                "workflow_tasks-MAX_NUM_FORMS": ["1000"],
                "workflow_tasks-0-task": [str(self.task_1.id)],
                "workflow_tasks-0-id": [str(self.workflow_task.id)],
                "workflow_tasks-0-ORDER": ["1"],
                "workflow_tasks-0-DELETE": [""],
                "workflow_tasks-1-task": [str(self.task_2.id)],
                "workflow_tasks-1-id": [""],
                "workflow_tasks-1-ORDER": ["2"],
                "workflow_tasks-1-DELETE": [""],
                "pages-TOTAL_FORMS": ["2"],
                "pages-INITIAL_FORMS": ["1"],
                "pages-MIN_NUM_FORMS": ["0"],
                "pages-MAX_NUM_FORMS": ["1000"],
                "pages-0-page": [str(self.page.id)],
                "pages-0-DELETE": [""],
                "pages-1-page": [str(self.page.id)],
                "pages-1-DELETE": [""],
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormsetError(
            response,
            "pages_formset",
            None,
            None,
            ["You cannot assign this workflow to the same page multiple times."],
        )

    def test_pages_ignored_if_workflow_disabled(self):
        self.workflow.active = False
        self.workflow.save()
        self.workflow.workflow_pages.all().delete()

        response = self.post(
            {
                "name": [str(self.workflow.name)],
                "active": ["on"],
                "workflow_tasks-TOTAL_FORMS": ["2"],
                "workflow_tasks-INITIAL_FORMS": ["1"],
                "workflow_tasks-MIN_NUM_FORMS": ["0"],
                "workflow_tasks-MAX_NUM_FORMS": ["1000"],
                "workflow_tasks-0-task": [str(self.task_1.id)],
                "workflow_tasks-0-id": [str(self.workflow_task.id)],
                "workflow_tasks-0-ORDER": ["1"],
                "workflow_tasks-0-DELETE": [""],
                "workflow_tasks-1-task": [str(self.task_2.id)],
                "workflow_tasks-1-id": [""],
                "workflow_tasks-1-ORDER": ["2"],
                "workflow_tasks-1-DELETE": [""],
                "pages-TOTAL_FORMS": ["2"],
                "pages-INITIAL_FORMS": ["1"],
                "pages-MIN_NUM_FORMS": ["0"],
                "pages-MAX_NUM_FORMS": ["1000"],
                "pages-0-page": [str(self.page.id)],
                "pages-0-DELETE": [""],
                "pages-1-page": [""],
                "pages-1-DELETE": [""],
            }
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailadmin_workflows:index"))

        # Check that the pages weren't added to the workflow
        self.workflow.refresh_from_db()
        self.assertFalse(self.workflow.workflow_pages.exists())


class TestRemoveWorkflow(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        delete_existing_workflows()
        self.login()
        self.workflow = Workflow.objects.create(name="workflow")
        self.page = Page.objects.first()
        WorkflowPage.objects.create(workflow=self.workflow, page=self.page)

        self.editor = self.create_user(
            username="editor",
            email="editor@email.com",
            password="password",
        )
        editors = Group.objects.get(name="Editors")
        editors.user_set.add(self.editor)

        self.moderator = self.create_user(
            username="moderator",
            email="moderator@email.com",
            password="password",
        )
        moderators = Group.objects.get(name="Moderators")
        moderators.user_set.add(self.moderator)
        moderators.permissions.add(Permission.objects.get(codename="change_workflow"))

    def post(self, post_data={}):
        return self.client.post(
            reverse(
                "wagtailadmin_workflows:remove", args=[self.page.id, self.workflow.id]
            ),
            post_data,
        )

    def test_post(self):
        # Check that a WorkflowPage instance is removed correctly
        self.post()
        self.assertEqual(
            WorkflowPage.objects.filter(workflow=self.workflow, page=self.page).count(),
            0,
        )

    def test_no_permissions(self):
        self.login(user=self.editor)
        response = self.post()
        self.assertEqual(response.status_code, 302)

    def test_post_with_permission(self):
        self.login(user=self.moderator)
        response = self.post()
        self.assertEqual(response.status_code, 302)


class TestTaskIndexView(TestCase, WagtailTestUtils):
    def setUp(self):
        delete_existing_workflows()
        self.login()

        self.editor = self.create_user(
            username="editor",
            email="editor@email.com",
            password="password",
        )
        editors = Group.objects.get(name="Editors")
        editors.user_set.add(self.editor)

        self.moderator = self.create_user(
            username="moderator",
            email="moderator@email.com",
            password="password",
        )
        moderators = Group.objects.get(name="Moderators")
        moderators.user_set.add(self.moderator)
        moderators.permissions.add(Permission.objects.get(codename="change_task"))

    def get(self, params={}):
        return self.client.get(reverse("wagtailadmin_workflows:task_index"), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/workflows/task_index.html")

        # Initially there should be no tasks listed
        self.assertContains(response, "There are no enabled tasks")

        SimpleTask.objects.create(name="test_task", active=True)

        # Now the listing should contain our task
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/workflows/task_index.html")
        self.assertNotContains(response, "There are no enabled tasks")
        self.assertContains(response, "test_task")

    def test_deactivated(self):
        Task.objects.create(name="test_task", active=False)

        # The listing should contain our task, as well as marking it as disabled
        response = self.get(params={"show_disabled": "true"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "No tasks have been created.")
        self.assertContains(response, "test_task")
        self.assertContains(
            response, '<span class="status-tag">Disabled</span>', html=True
        )

        # The listing should not contain task if show_disabled query parameter is 'False'
        response = self.get(params={})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "There are no enabled tasks")
        self.assertNotContains(response, "test_task")

    def test_permissions(self):
        self.login(user=self.editor)
        response = self.get()
        self.assertEqual(response.status_code, 302)
        full_context = {
            key: value for context in response.context for key, value in context.items()
        }
        self.assertEqual(
            full_context["message"],
            "Sorry, you do not have permission to access this area.",
        )

        self.login(user=self.moderator)
        response = self.get()
        self.assertEqual(response.status_code, 200)


class TestCreateTaskView(TestCase, WagtailTestUtils):
    def setUp(self):
        delete_existing_workflows()
        self.login()

        self.editor = self.create_user(
            username="editor",
            email="editor@email.com",
            password="password",
        )
        editors = Group.objects.get(name="Editors")
        editors.user_set.add(self.editor)

        self.moderator = self.create_user(
            username="moderator",
            email="moderator@email.com",
            password="password",
        )
        moderators = Group.objects.get(name="Moderators")
        moderators.user_set.add(self.moderator)
        moderators.permissions.add(Permission.objects.get(codename="add_task"))

    def get(self, url_kwargs=None, params={}):
        url_kwargs = url_kwargs or {}
        url_kwargs.setdefault("app_label", SimpleTask._meta.app_label)
        url_kwargs.setdefault("model_name", SimpleTask._meta.model_name)
        return self.client.get(
            reverse("wagtailadmin_workflows:add_task", kwargs=url_kwargs), params
        )

    def post(self, post_data={}):
        return self.client.post(
            reverse(
                "wagtailadmin_workflows:add_task",
                kwargs={
                    "app_label": SimpleTask._meta.app_label,
                    "model_name": SimpleTask._meta.model_name,
                },
            ),
            post_data,
        )

    def test_get(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/workflows/create_task.html")

    def test_get_with_non_task_model(self):
        response = self.get(
            url_kwargs={"app_label": "wagtailcore", "model_name": "Site"}
        )
        self.assertEqual(response.status_code, 404)

    def test_get_with_base_task_model(self):
        response = self.get(
            url_kwargs={"app_label": "wagtailcore", "model_name": "Task"}
        )
        self.assertEqual(response.status_code, 404)

    def test_post(self):
        response = self.post({"name": "test_task", "active": "on"})

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailadmin_workflows:task_index"))

        # Check that the task was created
        tasks = Task.objects.filter(name="test_task", active=True)
        self.assertEqual(tasks.count(), 1)

    def test_permissions(self):
        self.login(user=self.editor)
        response = self.get()
        self.assertEqual(response.status_code, 302)
        full_context = {
            key: value for context in response.context for key, value in context.items()
        }
        self.assertEqual(
            full_context["message"],
            "Sorry, you do not have permission to access this area.",
        )

        self.login(user=self.moderator)
        response = self.get()
        self.assertEqual(response.status_code, 200)


class TestSelectTaskTypeView(TestCase, WagtailTestUtils):
    def setUp(self):
        delete_existing_workflows()
        self.login()

    def get(self):
        return self.client.get(reverse("wagtailadmin_workflows:select_task_type"))

    def test_get(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/workflows/select_task_type.html"
        )

        # Check that the list of available task types includes SimpleTask and GroupApprovalTask
        self.assertContains(response, SimpleTask.get_verbose_name())
        self.assertContains(response, GroupApprovalTask.get_verbose_name())
        self.assertContains(response, GroupApprovalTask.get_description())


class TestEditTaskView(TestCase, WagtailTestUtils):
    def setUp(self):
        delete_existing_workflows()
        self.login()
        self.task = GroupApprovalTask.objects.create(name="test_task")

        self.editor = self.create_user(
            username="editor",
            email="editor@email.com",
            password="password",
        )
        editors = Group.objects.get(name="Editors")
        editors.user_set.add(self.editor)

        self.moderator = self.create_user(
            username="moderator",
            email="moderator@email.com",
            password="password",
        )
        moderators = Group.objects.get(name="Moderators")
        moderators.user_set.add(self.moderator)
        moderators.permissions.add(Permission.objects.get(codename="change_task"))

    def get(self, params={}):
        return self.client.get(
            reverse("wagtailadmin_workflows:edit_task", args=[self.task.id]), params
        )

    def post(self, post_data={}):
        return self.client.post(
            reverse("wagtailadmin_workflows:edit_task", args=[self.task.id]), post_data
        )

    def test_get(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/workflows/edit_task.html")

    def test_post(self):
        self.assertEqual(self.task.groups.count(), 0)
        editors = Group.objects.get(name="Editors")

        response = self.post(
            {"name": "test_task_modified", "active": "on", "groups": [str(editors.id)]}
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailadmin_workflows:task_index"))

        # Check that the task was updated
        task = GroupApprovalTask.objects.get(id=self.task.id)

        # The task name cannot be changed
        self.assertEqual(task.name, "test_task")

        # This request should've added a group to the task
        self.assertEqual(task.groups.count(), 1)
        self.assertTrue(task.groups.filter(id=editors.id).exists())

    def test_permissions(self):
        self.login(user=self.editor)
        response = self.get()
        self.assertEqual(response.status_code, 302)
        full_context = {
            key: value for context in response.context for key, value in context.items()
        }
        self.assertEqual(
            full_context["message"],
            "Sorry, you do not have permission to access this area.",
        )

        self.login(user=self.moderator)
        response = self.get()
        self.assertEqual(response.status_code, 200)

    def test_admin_url_finder(self):
        editor_url_finder = AdminURLFinder(self.editor)
        self.assertIsNone(editor_url_finder.get_edit_url(self.task))
        moderator_url_finder = AdminURLFinder(self.moderator)
        expected_url = "/admin/workflows/tasks/edit/%d/" % self.task.pk
        self.assertEqual(moderator_url_finder.get_edit_url(self.task), expected_url)


class TestSubmitToWorkflow(TestCase, WagtailTestUtils):
    def setUp(self):
        delete_existing_workflows()
        self.submitter = self.create_user(
            username="submitter",
            email="submitter@email.com",
            password="password",
        )
        editors = Group.objects.get(name="Editors")
        editors.user_set.add(self.submitter)
        self.moderator = self.create_user(
            username="moderator",
            email="moderator@email.com",
            password="password",
        )
        moderators = Group.objects.get(name="Moderators")
        moderators.user_set.add(self.moderator)

        self.superuser = self.create_superuser(
            username="superuser",
            email="superuser@email.com",
            password="password",
        )

        self.login(user=self.submitter)

        # Create a page
        root_page = Page.objects.get(id=2)
        self.page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            content="hello",
            live=False,
            has_unpublished_changes=True,
        )
        root_page.add_child(instance=self.page)
        self.page.save_revision()

        self.workflow, self.task_1, self.task_2 = self.create_workflow_and_tasks()

        WorkflowPage.objects.create(workflow=self.workflow, page=self.page)

    def create_workflow_and_tasks(self):
        workflow = Workflow.objects.create(name="test_workflow")
        task_1 = GroupApprovalTask.objects.create(name="test_task_1")
        task_2 = GroupApprovalTask.objects.create(name="test_task_2")
        task_1.groups.set(Group.objects.filter(name="Moderators"))
        task_2.groups.set(Group.objects.filter(name="Moderators"))
        WorkflowTask.objects.create(workflow=workflow, task=task_1, sort_order=1)
        WorkflowTask.objects.create(workflow=workflow, task=task_2, sort_order=2)
        return workflow, task_1, task_2

    def submit(self):
        post_data = {
            "title": str(self.page.title),
            "slug": str(self.page.slug),
            "content": str(self.page.content),
            "action-submit": "True",
        }
        return self.client.post(
            reverse("wagtailadmin_pages:edit", args=(self.page.id,)), post_data
        )

    def test_submit_for_approval_creates_states(self):
        """Test that WorkflowState and TaskState objects are correctly created when a Page is submitted for approval"""

        self.submit()

        workflow_state = self.page.current_workflow_state

        self.assertEqual(type(workflow_state), WorkflowState)
        self.assertEqual(workflow_state.workflow, self.workflow)
        self.assertEqual(workflow_state.status, workflow_state.STATUS_IN_PROGRESS)
        self.assertEqual(workflow_state.requested_by, self.submitter)

        task_state = workflow_state.current_task_state

        self.assertEqual(type(task_state), TaskState)
        self.assertEqual(task_state.task.specific, self.task_1)
        self.assertEqual(task_state.status, task_state.STATUS_IN_PROGRESS)

    def test_submit_for_approval_changes_status_in_header_meta(self):
        edit_url = reverse("wagtailadmin_pages:edit", args=(self.page.id,))

        response = self.client.get(edit_url)
        self.assertContains(response, "Draft", count=1)

        # submit for approval
        self.submit()

        response = self.client.get(edit_url)
        workflow_status_url = reverse(
            "wagtailadmin_pages:workflow_status", args=(self.page.id,)
        )
        self.assertContains(response, workflow_status_url)
        self.assertRegex(
            response.content.decode("utf-8"),
            r"Awaiting[\s|\n]+{}".format(self.page.current_workflow_task.name),
        )
        self.assertNotContains(response, "Draft")

    def test_submit_sends_mail(self):
        self.submit()
        # 3 emails sent:
        # - to moderator - submitted for approval in moderation stage test_task_1
        # - to superuser - submitted for approval in moderation stage test_task_1
        # - to superuser - submitted to workflow test_workflow
        self.assertEqual(len(mail.outbox), 3)

        # the 'submitted to workflow' email should include the submitter's name
        workflow_message = None
        for msg in mail.outbox:
            if (
                msg.subject
                == 'The page "Hello world! (simple page)" has been submitted to workflow "test_workflow"'
            ):
                workflow_message = msg
                break

        self.assertTrue(workflow_message)
        self.assertIn(
            'The page "Hello world! (simple page)" has been submitted for moderation to workflow "test_workflow" by submitter',
            workflow_message.body,
        )

    @mock.patch.object(
        EmailMultiAlternatives, "send", side_effect=IOError("Server down")
    )
    def test_email_send_error(self, mock_fn):
        logging.disable(logging.CRITICAL)

        response = self.submit()
        logging.disable(logging.NOTSET)

        # An email that fails to send should return a message rather than crash the page
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse("wagtailadmin_home"))

    def test_resume_rejected_workflow(self):
        # test that an existing workflow can be resumed by submitting when rejected
        self.workflow.start(self.page, user=self.submitter)
        workflow_state = self.page.current_workflow_state
        workflow_state.current_task_state.approve(user=self.superuser)
        workflow_state.refresh_from_db()
        workflow_state.current_task_state.reject(user=self.superuser)
        workflow_state.refresh_from_db()
        self.assertEqual(workflow_state.current_task_state.task.specific, self.task_2)
        self.assertEqual(workflow_state.status, WorkflowState.STATUS_NEEDS_CHANGES)

        self.submit()
        workflow_state.refresh_from_db()

        # check that the same workflow state's status is now in progress
        self.assertEqual(workflow_state.status, WorkflowState.STATUS_IN_PROGRESS)

        # check that the workflow remains on the rejecting task, rather than resetting
        self.assertEqual(workflow_state.current_task_state.task.specific, self.task_2)

    def test_restart_rejected_workflow(self):
        # test that an existing workflow can be restarted when rejected
        self.workflow.start(self.page, user=self.submitter)
        workflow_state = self.page.current_workflow_state
        workflow_state.current_task_state.approve(user=self.superuser)
        workflow_state.refresh_from_db()
        workflow_state.current_task_state.reject(user=self.superuser)
        workflow_state.refresh_from_db()
        self.assertEqual(workflow_state.current_task_state.task.specific, self.task_2)
        self.assertEqual(workflow_state.status, WorkflowState.STATUS_NEEDS_CHANGES)

        post_data = {
            "title": str(self.page.title),
            "slug": str(self.page.slug),
            "content": str(self.page.content),
            "action-restart-workflow": "True",
        }
        self.client.post(
            reverse("wagtailadmin_pages:edit", args=(self.page.id,)), post_data
        )
        workflow_state.refresh_from_db()

        # check that the same workflow state's status is now cancelled
        self.assertEqual(workflow_state.status, WorkflowState.STATUS_CANCELLED)

        # check that the new workflow has started on the first task
        new_workflow_state = self.page.current_workflow_state
        self.assertEqual(new_workflow_state.status, WorkflowState.STATUS_IN_PROGRESS)
        self.assertEqual(
            new_workflow_state.current_task_state.task.specific, self.task_1
        )

    def test_cancel_workflow(self):
        # test that an existing workflow can be cancelled after submission by the submitter
        self.workflow.start(self.page, user=self.submitter)
        workflow_state = self.page.current_workflow_state
        self.assertEqual(workflow_state.current_task_state.task.specific, self.task_1)
        self.assertEqual(workflow_state.status, WorkflowState.STATUS_IN_PROGRESS)
        post_data = {
            "title": str(self.page.title),
            "slug": str(self.page.slug),
            "content": str(self.page.content),
            "action-cancel-workflow": "True",
        }
        self.client.post(
            reverse("wagtailadmin_pages:edit", args=(self.page.id,)), post_data
        )
        workflow_state.refresh_from_db()

        # check that the workflow state's status is now cancelled
        self.assertEqual(workflow_state.status, WorkflowState.STATUS_CANCELLED)
        self.assertEqual(
            workflow_state.current_task_state.status, TaskState.STATUS_CANCELLED
        )

    def test_email_headers(self):
        # Submit
        self.submit()

        msg_headers = set(mail.outbox[0].message().items())
        headers = {("Auto-Submitted", "auto-generated")}
        self.assertTrue(
            headers.issubset(msg_headers),
            msg="Message is missing the Auto-Submitted header.",
        )


@freeze_time("2020-03-31 12:00:00")
class TestApproveRejectWorkflow(TestCase, WagtailTestUtils):
    def setUp(self):
        delete_existing_workflows()
        self.submitter = self.create_user(
            username="submitter",
            first_name="Sebastian",
            last_name="Mitter",
            email="submitter@email.com",
            password="password",
        )
        editors = Group.objects.get(name="Editors")
        editors.user_set.add(self.submitter)
        self.moderator = self.create_user(
            username="moderator",
            email="moderator@email.com",
            password="password",
        )
        moderators = Group.objects.get(name="Moderators")
        moderators.user_set.add(self.moderator)

        self.superuser = self.create_superuser(
            username="superuser",
            email="superuser@email.com",
            password="password",
        )

        self.login(user=self.submitter)

        # Create a page
        root_page = Page.objects.get(id=2)
        self.page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            content="hello",
            live=False,
            has_unpublished_changes=True,
        )
        root_page.add_child(instance=self.page)

        self.workflow, self.task_1 = self.create_workflow_and_tasks()

        WorkflowPage.objects.create(workflow=self.workflow, page=self.page)

        self.submit()

        self.login(user=self.moderator)

    def create_workflow_and_tasks(self):
        workflow = Workflow.objects.create(name="test_workflow")
        task_1 = GroupApprovalTask.objects.create(name="test_task_1")
        task_1.groups.set(Group.objects.filter(name="Moderators"))
        WorkflowTask.objects.create(workflow=workflow, task=task_1, sort_order=1)
        return workflow, task_1

    def submit(self):
        post_data = {
            "title": str(self.page.title),
            "slug": str(self.page.slug),
            "content": str(self.page.content),
            "action-submit": "True",
        }
        return self.client.post(
            reverse("wagtailadmin_pages:edit", args=(self.page.id,)), post_data
        )

    @override_settings(WAGTAIL_FINISH_WORKFLOW_ACTION="")
    def test_approve_task_and_workflow(self):
        """
        This posts to the approve task view and checks that the page was approved and published
        """
        # Unset WAGTAIL_FINISH_WORKFLOW_ACTION - default action should be to publish
        del settings.WAGTAIL_FINISH_WORKFLOW_ACTION
        # Connect a mock signal handler to page_published signal
        mock_handler = mock.MagicMock()
        page_published.connect(mock_handler)

        # Post
        self.client.post(
            reverse(
                "wagtailadmin_pages:workflow_action",
                args=(
                    self.page.id,
                    "approve",
                    self.page.current_workflow_task_state.id,
                ),
            ),
            {"comment": "my comment"},
        )

        # Check that the workflow was approved

        workflow_state = WorkflowState.objects.get(
            page=self.page, requested_by=self.submitter
        )

        self.assertEqual(workflow_state.status, workflow_state.STATUS_APPROVED)

        # Check that the task was approved

        task_state = workflow_state.current_task_state

        self.assertEqual(task_state.status, task_state.STATUS_APPROVED)

        # Check that the comment was added to the task state correctly

        self.assertEqual(task_state.comment, "my comment")

        page = Page.objects.get(id=self.page.id)
        # Page must be live
        self.assertTrue(page.live, "Approving moderation failed to set live=True")
        # Page should now have no unpublished changes
        self.assertFalse(
            page.has_unpublished_changes,
            "Approving moderation failed to set has_unpublished_changes=False",
        )

        # Check that the page_published signal was fired
        self.assertEqual(mock_handler.call_count, 1)
        mock_call = mock_handler.mock_calls[0][2]

        self.assertEqual(mock_call["sender"], self.page.specific_class)
        self.assertEqual(mock_call["instance"], self.page)
        self.assertIsInstance(mock_call["instance"], self.page.specific_class)

    def test_workflow_dashboard_panel(self):
        response = self.client.get(reverse("wagtailadmin_home"))
        self.assertContains(response, "Awaiting your review")
        # check that ActivateWorkflowActionsForDashboard is present and passes a valid csrf token
        self.assertRegex(
            response.content.decode("utf-8"),
            r"ActivateWorkflowActionsForDashboard\(\'\w+\'\)",
        )

    def test_workflow_action_get(self):
        """
        This tests that a GET request to the workflow action view (for the approve action) returns a modal with a form for extra data entry:
        adding a comment
        """
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:workflow_action",
                args=(
                    self.page.id,
                    "approve",
                    self.page.current_workflow_task_state.id,
                ),
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/pages/workflow_action_modal.html"
        )
        html = json.loads(response.content)["html"]
        self.assertTagInHTML(
            '<form action="'
            + reverse(
                "wagtailadmin_pages:workflow_action",
                args=(
                    self.page.id,
                    "approve",
                    self.page.current_workflow_task_state.id,
                ),
            )
            + '" method="POST" novalidate>',
            html,
        )
        self.assertIn("Comment", html)

    def test_workflow_action_view_bad_page_id(self):
        """
        This tests that the workflow action view handles invalid page ids correctly
        """
        # Post
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:workflow_action",
                args=(
                    127777777777,
                    "approve",
                    self.page.current_workflow_task_state.id,
                ),
            )
        )

        # Check that the user received a 404 response
        self.assertEqual(response.status_code, 404)

    def test_workflow_action_view_not_in_group(self):
        """
        This tests that the workflow action view for a GroupApprovalTask won't allow approval from a user not in the
        specified group/a superuser
        """
        # Remove privileges from user
        self.login(user=self.submitter)

        # Post
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:workflow_action",
                args=(
                    self.page.id,
                    "approve",
                    self.page.current_workflow_task_state.id,
                ),
            )
        )
        # Check that the user received a permission denied response
        self.assertRedirects(response, "/admin/")

    def test_edit_view_workflow_cancellation_not_in_group(self):
        """
        This tests that the page edit view for a GroupApprovalTask, locked to a user not in the
        specified group/a superuser, still allows the submitter to cancel workflows
        """
        self.login(user=self.submitter)

        # Post
        response = self.client.post(
            reverse("wagtailadmin_pages:edit", args=(self.page.id,)),
            {"action-cancel-workflow": "True"},
        )

        # Check that the user received a 200 response
        self.assertEqual(response.status_code, 200)

        # Check that the workflow state was marked as cancelled
        workflow_state = WorkflowState.objects.get(
            page=self.page, requested_by=self.submitter
        )
        self.assertEqual(workflow_state.status, WorkflowState.STATUS_CANCELLED)

    def test_reject_task_and_workflow(self):
        """
        This posts to the reject task view and checks that the page was rejected and not published
        """
        # Post
        self.client.post(
            reverse(
                "wagtailadmin_pages:workflow_action",
                args=(self.page.id, "reject", self.page.current_workflow_task_state.id),
            )
        )

        # Check that the workflow was marked as needing changes

        workflow_state = WorkflowState.objects.get(
            page=self.page, requested_by=self.submitter
        )

        self.assertEqual(workflow_state.status, workflow_state.STATUS_NEEDS_CHANGES)

        # Check that the task was rejected

        task_state = workflow_state.current_task_state

        self.assertEqual(task_state.status, task_state.STATUS_REJECTED)

        page = Page.objects.get(id=self.page.id)
        # Page must not be live
        self.assertFalse(page.live)

    def test_workflow_action_view_rejection_not_in_group(self):
        """
        This tests that the workflow action view for a GroupApprovalTask won't allow rejection from a user not in the
        specified group/a superuser
        """
        # Remove privileges from user
        self.login(user=self.submitter)

        # Post
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:workflow_action",
                args=(self.page.id, "reject", self.page.current_workflow_task_state.id),
            )
        )

        # Check that the user received a permission denied response
        self.assertRedirects(response, "/admin/")

    def test_collect_workflow_action_data_get(self):
        """
        This tests that a GET request to the collect_workflow_action_data view (for the approve action) returns a modal with a form for extra data entry:
        adding a comment
        """
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:collect_workflow_action_data",
                args=(
                    self.page.id,
                    "approve",
                    self.page.current_workflow_task_state.id,
                ),
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/pages/workflow_action_modal.html"
        )
        self.assertTemplateUsed(response, "wagtailadmin/shared/non_field_errors.html")
        html = json.loads(response.content)["html"]
        self.assertTagInHTML(
            '<form action="'
            + reverse(
                "wagtailadmin_pages:collect_workflow_action_data",
                args=(
                    self.page.id,
                    "approve",
                    self.page.current_workflow_task_state.id,
                ),
            )
            + '" method="POST" novalidate>',
            html,
        )
        self.assertIn("Comment", html)

    def test_collect_workflow_action_data_post(self):
        """
        This tests that a POST request to the collect_workflow_action_data view (for the approve action) returns a modal response with the validated data
        """
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:collect_workflow_action_data",
                args=(
                    self.page.id,
                    "approve",
                    self.page.current_workflow_task_state.id,
                ),
            ),
            {"comment": "This is my comment"},
        )
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content)
        self.assertEqual(response_json["step"], "success")
        self.assertEqual(
            response_json["cleaned_data"], {"comment": "This is my comment"}
        )

    def test_workflow_action_via_edit_view(self):
        """
        Posting to the 'edit' view with 'action-workflow-action' set should perform the given workflow action in addition to updating page content
        """
        # Post
        self.client.post(
            reverse("wagtailadmin_pages:edit", args=(self.page.id,)),
            {
                "title": "This title was edited while approving",
                "slug": str(self.page.slug),
                "content": str(self.page.content),
                "action-workflow-action": "True",
                "workflow-action-name": "approve",
                "workflow-action-extra-data": '{"comment": "my comment"}',
            },
        )

        # Check that the workflow was approved

        workflow_state = WorkflowState.objects.get(
            page=self.page, requested_by=self.submitter
        )

        self.assertEqual(workflow_state.status, workflow_state.STATUS_APPROVED)

        # Check that the task was approved

        task_state = workflow_state.current_task_state

        self.assertEqual(task_state.status, task_state.STATUS_APPROVED)

        # Check that the comment was added to the task state correctly

        self.assertEqual(task_state.comment, "my comment")

        # Check that page edits made at the same time as the action have been saved
        page = Page.objects.get(id=self.page.id)
        self.assertEqual(
            page.get_latest_revision_as_page().title,
            "This title was edited while approving",
        )

    def test_workflow_report(self):
        response = self.client.get(reverse("wagtailadmin_reports:workflow"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello world!")
        self.assertContains(response, "test_workflow")
        self.assertContains(response, "Sebastian Mitter")
        self.assertContains(response, "March 31, 2020")

        response = self.client.get(reverse("wagtailadmin_reports:workflow_tasks"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello world!")

    def test_workflow_report_filtered(self):
        # the moderator can review the task, so the workflow state should show up even when reports are filtered by reviewable
        response = self.client.get(
            reverse("wagtailadmin_reports:workflow"), {"reviewable": "true"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello world!")
        self.assertContains(response, "test_workflow")
        self.assertContains(response, "Sebastian Mitter")
        self.assertContains(response, "March 31, 2020")

        response = self.client.get(
            reverse("wagtailadmin_reports:workflow_tasks"), {"reviewable": "true"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello world!")

        # the submitter cannot review the task, so the workflow state shouldn't show up when reports are filtered by reviewable
        self.login(self.submitter)
        response = self.client.get(
            reverse("wagtailadmin_reports:workflow"), {"reviewable": "true"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Hello world!")
        self.assertNotContains(response, "Sebastian Mitter")
        self.assertNotContains(response, "March 31, 2020")

        response = self.client.get(
            reverse("wagtailadmin_reports:workflow_tasks"), {"reviewable": "true"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Hello world!")


class TestNotificationPreferences(TestCase, WagtailTestUtils):
    def setUp(self):
        delete_existing_workflows()
        self.submitter = self.create_user(
            username="submitter",
            email="submitter@email.com",
            password="password",
        )
        editors = Group.objects.get(name="Editors")
        editors.user_set.add(self.submitter)
        self.moderator = self.create_user(
            username="moderator",
            email="moderator@email.com",
            password="password",
        )
        self.moderator2 = self.create_user(
            username="moderator2",
            email="moderator2@email.com",
            password="password",
        )
        moderators = Group.objects.get(name="Moderators")
        moderators.user_set.add(self.moderator)
        moderators.user_set.add(self.moderator2)

        self.superuser = self.create_superuser(
            username="superuser",
            email="superuser@email.com",
            password="password",
        )

        self.superuser_profile = UserProfile.get_for_user(self.superuser)
        self.moderator2_profile = UserProfile.get_for_user(self.moderator2)
        self.submitter_profile = UserProfile.get_for_user(self.submitter)

        # Create a page
        root_page = Page.objects.get(id=2)
        self.page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            content="hello",
            live=False,
            has_unpublished_changes=True,
        )
        root_page.add_child(instance=self.page)

        self.workflow, self.task_1 = self.create_workflow_and_tasks()

        WorkflowPage.objects.create(workflow=self.workflow, page=self.page)

    def create_workflow_and_tasks(self):
        workflow = Workflow.objects.create(name="test_workflow")
        task_1 = GroupApprovalTask.objects.create(name="test_task_1")
        task_1.groups.set(Group.objects.filter(name="Moderators"))
        WorkflowTask.objects.create(workflow=workflow, task=task_1, sort_order=1)
        return workflow, task_1

    def submit(self):
        post_data = {
            "title": str(self.page.title),
            "slug": str(self.page.slug),
            "content": str(self.page.content),
            "action-submit": "True",
        }
        return self.client.post(
            reverse("wagtailadmin_pages:edit", args=(self.page.id,)), post_data
        )

    def approve(self):
        return self.client.post(
            reverse(
                "wagtailadmin_pages:workflow_action",
                args=(
                    self.page.id,
                    "approve",
                    self.page.current_workflow_task_state.id,
                ),
            )
        )

    def reject(self):
        return self.client.post(
            reverse(
                "wagtailadmin_pages:workflow_action",
                args=(self.page.id, "reject", self.page.current_workflow_task_state.id),
            )
        )

    def test_vanilla_profile(self):
        # Check that the vanilla profile has rejected notifications on
        self.assertIs(self.submitter_profile.rejected_notifications, True)

        # Check that the vanilla profile has approved notifications on
        self.assertIs(self.submitter_profile.approved_notifications, True)

    @override_settings(WAGTAILADMIN_NOTIFICATION_INCLUDE_SUPERUSERS=True)
    def test_submitted_email_notifications_sent(self):
        """Test that 'submitted' notifications for WorkflowState and TaskState are both sent correctly"""
        self.login(self.submitter)
        self.submit()

        self.assertEqual(len(mail.outbox), 4)

        task_submission_emails = [
            email for email in mail.outbox if "task" in email.subject
        ]
        task_submission_emailed_addresses = [
            address for email in task_submission_emails for address in email.to
        ]
        workflow_submission_emails = [
            email for email in mail.outbox if "workflow" in email.subject
        ]
        workflow_submission_emailed_addresses = [
            address for email in workflow_submission_emails for address in email.to
        ]

        self.assertEqual(len(task_submission_emails), 3)
        # the moderator is in the Group assigned to the GroupApproval task, so should get an email
        self.assertIn(self.moderator.email, task_submission_emailed_addresses)
        self.assertIn(self.moderator2.email, task_submission_emailed_addresses)
        # with `WAGTAILADMIN_NOTIFICATION_INCLUDE_SUPERUSERS`, the superuser should get a task email
        self.assertIn(self.superuser.email, task_submission_emailed_addresses)
        # the submitter triggered this workflow update, so should not get an email
        self.assertNotIn(self.submitter.email, task_submission_emailed_addresses)

        self.assertEqual(len(workflow_submission_emails), 1)
        # the moderator should not get a workflow email
        self.assertNotIn(self.moderator.email, workflow_submission_emailed_addresses)
        self.assertNotIn(self.moderator2.email, workflow_submission_emailed_addresses)
        # with `WAGTAILADMIN_NOTIFICATION_INCLUDE_SUPERUSERS`, the superuser should get a workflow email
        self.assertIn(self.superuser.email, workflow_submission_emailed_addresses)
        # as the submitter was the triggering user, the submitter should not get an email notification
        self.assertNotIn(self.submitter.email, workflow_submission_emailed_addresses)

    @override_settings(WAGTAILADMIN_NOTIFICATION_INCLUDE_SUPERUSERS=False)
    def test_submitted_email_notifications_superuser_settings(self):
        """Test that 'submitted' notifications for WorkflowState and TaskState are not sent to superusers if
        `WAGTAILADMIN_NOTIFICATION_INCLUDE_SUPERUSERS=False`"""
        self.login(self.submitter)
        self.submit()

        task_submission_emails = [
            email for email in mail.outbox if "task" in email.subject
        ]
        task_submission_emailed_addresses = [
            address for email in task_submission_emails for address in email.to
        ]
        workflow_submission_emails = [
            email for email in mail.outbox if "workflow" in email.subject
        ]
        workflow_submission_emailed_addresses = [
            address for email in workflow_submission_emails for address in email.to
        ]

        # with `WAGTAILADMIN_NOTIFICATION_INCLUDE_SUPERUSERS` off, the superuser should not get a task email
        self.assertNotIn(self.superuser.email, task_submission_emailed_addresses)

        # with `WAGTAILADMIN_NOTIFICATION_INCLUDE_SUPERUSERS` off, the superuser should not get a workflow email
        self.assertNotIn(self.superuser.email, workflow_submission_emailed_addresses)

    @override_settings(WAGTAILADMIN_NOTIFICATION_INCLUDE_SUPERUSERS=True)
    def test_submit_notification_active_users_only(self):
        # moderator2 is inactive
        self.moderator2.is_active = False
        self.moderator2.save()

        # superuser is inactive
        self.superuser.is_active = False
        self.superuser.save()

        # Submit
        self.login(self.submitter)
        self.submit()

        workflow_submission_emails = [
            email for email in mail.outbox if "workflow" in email.subject
        ]
        workflow_submission_emailed_addresses = [
            address for email in workflow_submission_emails for address in email.to
        ]
        task_submission_emails = [
            email for email in mail.outbox if "task" in email.subject
        ]
        task_submission_emailed_addresses = [
            address for email in task_submission_emails for address in email.to
        ]

        # Check that moderator2 didn't receive a task submitted email
        self.assertNotIn(self.moderator2.email, task_submission_emailed_addresses)

        # Check that the superuser didn't receive a workflow or task email
        self.assertNotIn(self.superuser.email, task_submission_emailed_addresses)
        self.assertNotIn(self.superuser.email, workflow_submission_emailed_addresses)

    @override_settings(WAGTAILADMIN_NOTIFICATION_INCLUDE_SUPERUSERS=True)
    def test_submit_notification_preferences_respected(self):
        # moderator2 doesn't want emails
        self.moderator2_profile.submitted_notifications = False
        self.moderator2_profile.save()

        # superuser doesn't want emails
        self.superuser_profile.submitted_notifications = False
        self.superuser_profile.save()

        # Submit
        self.login(self.submitter)
        self.submit()

        # Check that only one moderator got a task submitted email
        workflow_submission_emails = [
            email for email in mail.outbox if "workflow" in email.subject
        ]
        workflow_submission_emailed_addresses = [
            address for email in workflow_submission_emails for address in email.to
        ]
        task_submission_emails = [
            email for email in mail.outbox if "task" in email.subject
        ]
        task_submission_emailed_addresses = [
            address for email in task_submission_emails for address in email.to
        ]
        self.assertNotIn(self.moderator2.email, task_submission_emailed_addresses)

        # Check that the superuser didn't receive a workflow or task email
        self.assertNotIn(self.superuser.email, task_submission_emailed_addresses)
        self.assertNotIn(self.superuser.email, workflow_submission_emailed_addresses)

    def test_approved_notifications(self):
        self.login(self.submitter)
        self.submit()
        # Approve
        self.login(self.moderator)
        self.approve()

        # Submitter must receive a workflow approved email
        workflow_approved_emails = [
            email
            for email in mail.outbox
            if ("workflow" in email.subject and "approved" in email.subject)
        ]
        self.assertEqual(len(workflow_approved_emails), 1)
        self.assertIn(self.submitter.email, workflow_approved_emails[0].to)

    def test_approved_notifications_preferences_respected(self):
        # Submitter doesn't want 'approved' emails
        self.submitter_profile.approved_notifications = False
        self.submitter_profile.save()

        self.login(self.submitter)
        self.submit()
        # Approve
        self.login(self.moderator)
        self.approve()

        # Submitter must not receive a workflow approved email, so there should be no emails in workflow_approved_emails
        workflow_approved_emails = [
            email
            for email in mail.outbox
            if ("workflow" in email.subject and "approved" in email.subject)
        ]
        self.assertEqual(len(workflow_approved_emails), 0)

    def test_rejected_notifications(self):
        self.login(self.submitter)
        self.submit()
        # Reject
        self.login(self.moderator)
        self.reject()

        # Submitter must receive a workflow rejected email
        workflow_rejected_emails = [
            email
            for email in mail.outbox
            if ("workflow" in email.subject and "rejected" in email.subject)
        ]
        self.assertEqual(len(workflow_rejected_emails), 1)
        self.assertIn(self.submitter.email, workflow_rejected_emails[0].to)

    def test_rejected_notification_preferences_respected(self):
        # Submitter doesn't want 'rejected' emails
        self.submitter_profile.rejected_notifications = False
        self.submitter_profile.save()

        self.login(self.submitter)
        self.submit()
        # Reject
        self.login(self.moderator)
        self.reject()

        # Submitter must not receive a workflow rejected email
        workflow_rejected_emails = [
            email
            for email in mail.outbox
            if ("workflow" in email.subject and "rejected" in email.subject)
        ]
        self.assertEqual(len(workflow_rejected_emails), 0)


class TestDisableViews(TestCase, WagtailTestUtils):
    def setUp(self):
        delete_existing_workflows()
        self.submitter = self.create_user(
            username="submitter",
            email="submitter@email.com",
            password="password",
        )
        editors = Group.objects.get(name="Editors")
        editors.user_set.add(self.submitter)
        self.moderator = self.create_user(
            username="moderator",
            email="moderator@email.com",
            password="password",
        )
        self.moderator2 = self.create_user(
            username="moderator2",
            email="moderator2@email.com",
            password="password",
        )
        moderators = Group.objects.get(name="Moderators")
        moderators.user_set.add(self.moderator)
        moderators.user_set.add(self.moderator2)

        self.superuser = self.create_superuser(
            username="superuser",
            email="superuser@email.com",
            password="password",
        )

        # Create a page
        root_page = Page.objects.get(id=2)
        self.page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            content="hello",
            live=False,
            has_unpublished_changes=True,
        )
        root_page.add_child(instance=self.page)

        self.workflow, self.task_1, self.task_2 = self.create_workflow_and_tasks()

        WorkflowPage.objects.create(workflow=self.workflow, page=self.page)

    def create_workflow_and_tasks(self):
        workflow = Workflow.objects.create(name="test_workflow")
        task_1 = GroupApprovalTask.objects.create(name="test_task_1")
        task_1.groups.set(Group.objects.filter(name="Moderators"))
        task_2 = GroupApprovalTask.objects.create(name="test_task_2")
        task_2.groups.set(Group.objects.filter(name="Moderators"))
        WorkflowTask.objects.create(workflow=workflow, task=task_1, sort_order=1)
        WorkflowTask.objects.create(workflow=workflow, task=task_2, sort_order=2)
        return workflow, task_1, task_2

    def submit(self):
        post_data = {
            "title": str(self.page.title),
            "slug": str(self.page.slug),
            "content": str(self.page.content),
            "action-submit": "True",
        }
        return self.client.post(
            reverse("wagtailadmin_pages:edit", args=(self.page.id,)), post_data
        )

    def approve(self):
        return self.client.post(
            reverse(
                "wagtailadmin_pages:workflow_action",
                args=(
                    self.page.id,
                    "approve",
                    self.page.current_workflow_task_state.id,
                ),
            )
        )

    def test_disable_workflow(self):
        """Test that deactivating a workflow sets it to inactive and cancels in progress states"""
        self.login(self.submitter)
        self.submit()
        self.login(self.superuser)
        self.approve()

        response = self.client.post(
            reverse("wagtailadmin_workflows:disable", args=(self.workflow.pk,))
        )
        self.assertEqual(response.status_code, 302)
        self.workflow.refresh_from_db()
        self.assertIs(self.workflow.active, False)
        states = WorkflowState.objects.filter(page=self.page, workflow=self.workflow)
        self.assertEqual(
            states.filter(status=WorkflowState.STATUS_IN_PROGRESS).count(), 0
        )
        self.assertEqual(
            states.filter(status=WorkflowState.STATUS_CANCELLED).count(), 1
        )

        self.assertEqual(
            TaskState.objects.filter(
                workflow_state__workflow=self.workflow,
                status=TaskState.STATUS_IN_PROGRESS,
            ).count(),
            0,
        )

    def test_disable_task_view(self):
        """Test that a view is shown before disabling a task that shows a warning"""
        self.login(self.submitter)
        self.submit()
        self.login(self.superuser)

        response = self.client.get(
            reverse("wagtailadmin_workflows:disable_task", args=(self.task_1.pk,))
        )

        self.assertTemplateUsed(
            response, "wagtailadmin/workflows/confirm_disable_task.html"
        )
        self.assertEqual(
            response.context["warning_message"],
            "This task is in progress on 1 page. Disabling this task will cause it to be skipped in the moderation workflow and not be listed for selection when editing a workflow.",
        )

        # create a new, unused, task and check the warning message is accurate
        unused_task = GroupApprovalTask.objects.create(name="unused_task_3")
        unused_task.groups.set(Group.objects.filter(name="Moderators"))

        response = self.client.get(
            reverse("wagtailadmin_workflows:disable_task", args=(unused_task.pk,))
        )

        self.assertEqual(
            response.context["warning_message"],
            "This task is in progress on 0 pages. Disabling this task will cause it to be skipped in the moderation workflow and not be listed for selection when editing a workflow.",
        )

        unused_task.delete()  # clean up

    def test_disable_task(self):
        """Test that deactivating a task sets it to inactive and cancels in progress states"""
        self.login(self.submitter)
        self.submit()
        self.login(self.superuser)

        response = self.client.post(
            reverse("wagtailadmin_workflows:disable_task", args=(self.task_1.pk,))
        )
        self.assertEqual(response.status_code, 302)
        self.task_1.refresh_from_db()
        self.assertIs(self.task_1.active, False)
        states = TaskState.objects.filter(
            workflow_state__page=self.page, task=self.task_1.task_ptr
        )
        self.assertEqual(states.filter(status=TaskState.STATUS_IN_PROGRESS).count(), 0)
        self.assertEqual(states.filter(status=TaskState.STATUS_CANCELLED).count(), 1)

        # Check that the page's WorkflowState has moved on to the next active task
        self.assertEqual(
            self.page.current_workflow_state.current_task_state.task.specific,
            self.task_2,
        )

    def test_enable_workflow(self):
        self.login(self.superuser)
        self.workflow.active = False
        self.workflow.save()

        response = self.client.post(
            reverse("wagtailadmin_workflows:enable", args=(self.workflow.pk,))
        )
        self.assertEqual(response.status_code, 302)
        self.workflow.refresh_from_db()
        self.assertIs(self.workflow.active, True)

    def test_enable_task(self):
        self.login(self.superuser)
        self.task_1.active = False
        self.task_1.save()

        response = self.client.post(
            reverse("wagtailadmin_workflows:enable_task", args=(self.task_1.pk,))
        )
        self.assertEqual(response.status_code, 302)
        self.task_1.refresh_from_db()
        self.assertIs(self.task_1.active, True)


class TestTaskChooserView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        self.task_enabled = GroupApprovalTask.objects.create(name="Enabled foo")
        self.task_disabled = GroupApprovalTask.objects.create(
            name="Disabled foo", active=False
        )

    def test_get(self):
        response = self.client.get(reverse("wagtailadmin_workflows:task_chooser"))

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response, "wagtailadmin/workflows/task_chooser/chooser.html"
        )

        # Check that the "select task type" view was shown in the "new" tab
        self.assertTemplateUsed(
            response,
            "wagtailadmin/workflows/task_chooser/includes/select_task_type.html",
        )
        self.assertTemplateUsed(
            response, "wagtailadmin/workflows/task_chooser/includes/results.html"
        )
        self.assertTemplateNotUsed(
            response, "wagtailadmin/workflows/task_chooser/includes/create_form.html"
        )
        self.assertFalse(response.context["search_form"].is_searching())
        # check that only active (non-disabled) tasks are listed
        self.assertEqual(
            [task.name for task in response.context["tasks"].object_list],
            ["Enabled foo", "Moderators approval"],
        )

    def test_search(self):
        response = self.client.get(
            reverse("wagtailadmin_workflows:task_chooser_results") + "?q=foo"
        )

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response, "wagtailadmin/workflows/task_chooser/includes/results.html"
        )
        self.assertTemplateNotUsed(
            response, "wagtailadmin/workflows/task_chooser/chooser.html"
        )
        self.assertTrue(response.context["search_form"].is_searching())
        self.assertEqual(response.context["query_string"], "foo")
        # check that only active (non-disabled) tasks are listed
        self.assertEqual(
            [task.name for task in response.context["tasks"].object_list],
            ["Enabled foo"],
        )

    def test_pagination(self):
        response = self.client.get(
            reverse("wagtailadmin_workflows:task_chooser_results") + "?p=2"
        )

        self.assertEqual(response.status_code, 200)

        # When pagination is used, only the results template should be rendered
        self.assertTemplateUsed(
            response, "wagtailadmin/workflows/task_chooser/includes/results.html"
        )
        self.assertTemplateNotUsed(
            response, "wagtailadmin/workflows/task_chooser/chooser.html"
        )
        self.assertFalse(response.context["search_form"].is_searching())

    def test_get_with_create_model_selected(self):
        response = self.client.get(
            reverse("wagtailadmin_workflows:task_chooser_create")
            + "?create_model=wagtailcore.GroupApprovalTask"
        )

        self.assertEqual(response.status_code, 200)

        # Check that the "create" view was returned
        self.assertTemplateUsed(
            response, "wagtailadmin/workflows/task_chooser/includes/create_form.html"
        )
        self.assertTemplateNotUsed(
            response,
            "wagtailadmin/workflows/task_chooser/includes/select_task_type.html",
        )

    def test_get_with_non_task_create_model_selected(self):
        response = self.client.get(
            reverse("wagtailadmin_workflows:task_chooser_create")
            + "?create_model=wagtailcore.Page"
        )

        self.assertEqual(response.status_code, 404)

    def test_get_with_base_task_create_model_selected(self):
        # Task is technically a subclass of itself so we need an extra test for it
        response = self.client.get(
            reverse("wagtailadmin_workflows:task_chooser_create")
            + "?create_model=wagtailcore.Task"
        )

        self.assertEqual(response.status_code, 404)

    @mock.patch("wagtail.admin.views.workflows.get_task_types")
    def test_get_with_single_task_model(self, get_task_types):
        # When a single task type exists there's no need to specify create_model
        get_task_types.return_value = [GroupApprovalTask]

        response = self.client.get(reverse("wagtailadmin_workflows:task_chooser"))

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response, "wagtailadmin/workflows/task_chooser/chooser.html"
        )

        # Check that the "create" view was shown in the "new" tab
        self.assertTemplateUsed(
            response, "wagtailadmin/workflows/task_chooser/includes/create_form.html"
        )
        self.assertTemplateNotUsed(
            response,
            "wagtailadmin/workflows/task_chooser/includes/select_task_type.html",
        )

    # POST requests are for creating new tasks

    def get_post_data(self):
        return {
            "create-task-name": "Editor approval task",
            "create-task-groups": [str(Group.objects.get(name="Editors").id)],
        }

    def test_post_with_create_model_selected(self):
        response = self.client.post(
            reverse("wagtailadmin_workflows:task_chooser_create")
            + "?create_model=wagtailcore.GroupApprovalTask",
            self.get_post_data(),
        )

        self.assertEqual(response.status_code, 200)

        # Check that the task was created
        task = Task.objects.get(name="Editor approval task", active=True)

        # Check the response JSON
        self.assertEqual(
            response.json(),
            {
                "step": "task_chosen",
                "result": {
                    "id": task.id,
                    "name": "Editor approval task",
                    "edit_url": reverse(
                        "wagtailadmin_workflows:edit_task", args=[task.id]
                    ),
                },
            },
        )

    @mock.patch("wagtail.admin.views.workflows.get_task_types")
    def test_post_with_single_task_model(self, get_task_types):
        # When a single task type exists there's no need to specify create_model
        get_task_types.return_value = [GroupApprovalTask]

        response = self.client.post(
            reverse("wagtailadmin_workflows:task_chooser_create"), self.get_post_data()
        )

        self.assertEqual(response.status_code, 200)

        # Check that the task was created
        task = Task.objects.get(name="Editor approval task", active=True)

        # Check the response JSON
        self.assertEqual(
            response.json(),
            {
                "step": "task_chosen",
                "result": {
                    "id": task.id,
                    "name": "Editor approval task",
                    "edit_url": reverse(
                        "wagtailadmin_workflows:edit_task", args=[task.id]
                    ),
                },
            },
        )

    def test_post_without_create_model_selected(self):
        response = self.client.post(
            reverse("wagtailadmin_workflows:task_chooser_create"), self.get_post_data()
        )

        self.assertEqual(response.status_code, 400)

        # Check that the task wasn't created
        self.assertFalse(
            Task.objects.filter(name="Editor approval task", active=True).exists()
        )

    def test_post_with_non_task_create_model_selected(self):
        response = self.client.post(
            reverse("wagtailadmin_workflows:task_chooser_create")
            + "?create_model=wagtailcore.Page",
            self.get_post_data(),
        )

        self.assertEqual(response.status_code, 404)

        # Check that the task wasn't created
        self.assertFalse(
            Task.objects.filter(name="Editor approval task", active=True).exists()
        )

    def test_post_with_base_task_create_model_selected(self):
        # Task is technically a subclass of itself so we need an extra test for it
        response = self.client.post(
            reverse("wagtailadmin_workflows:task_chooser_create")
            + "?create_model=wagtailcore.Task",
            self.get_post_data(),
        )

        self.assertEqual(response.status_code, 404)

        # Check that the task wasn't created
        self.assertFalse(
            Task.objects.filter(name="Editor approval task", active=True).exists()
        )


class TestTaskChooserChosenView(TestCase, WagtailTestUtils):
    def setUp(self):
        delete_existing_workflows()
        self.login()
        self.task = SimpleTask.objects.create(name="test_task")

    def test_get(self):
        response = self.client.get(
            reverse("wagtailadmin_workflows:task_chosen", args=[self.task.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            response.json(),
            {
                "result": {
                    "edit_url": reverse(
                        "wagtailadmin_workflows:edit_task", args=[self.task.id]
                    ),
                    "id": self.task.id,
                    "name": "test_task",
                },
                "step": "task_chosen",
            },
        )


class TestWorkflowUsageView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()
        self.workflow = Workflow.objects.get()

        self.root_page = Page.objects.get(depth=1)
        self.home_page = Page.objects.get(depth=2)

        self.child_page_with_another_workflow = self.home_page.add_child(
            instance=SimplePage(title="Another page", content="I'm another page")
        )
        self.another_workflow = Workflow.objects.create(name="Another workflow")
        self.another_workflow.workflow_pages.create(
            page=self.child_page_with_another_workflow
        )

    def test_get(self):
        response = self.client.get(
            reverse("wagtailadmin_workflows:usage", args=[self.workflow.id])
        )

        self.assertEqual(response.status_code, 200)

        object_set = {page.id for page in response.context["used_by"].object_list}
        self.assertIn(self.root_page.id, object_set)
        self.assertIn(self.home_page.id, object_set)
        self.assertNotIn(self.child_page_with_another_workflow.id, object_set)


@freeze_time("2020-06-01 12:00:00")
class TestWorkflowStatus(TestCase, WagtailTestUtils):
    def setUp(self):
        delete_existing_workflows()
        self.submitter = self.create_user(
            username="submitter",
            email="submitter@email.com",
            password="password",
        )
        editors = Group.objects.get(name="Editors")
        editors.user_set.add(self.submitter)
        self.moderator = self.create_user(
            username="moderator",
            email="moderator@email.com",
            password="password",
        )
        moderators = Group.objects.get(name="Moderators")
        moderators.user_set.add(self.moderator)

        self.superuser = self.create_superuser(
            username="superuser",
            email="superuser@email.com",
            password="password",
        )

        self.login(self.superuser)

        # Create a page
        root_page = Page.objects.get(id=2)
        self.page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            content="hello",
            live=False,
            has_unpublished_changes=True,
        )
        root_page.add_child(instance=self.page)

        self.workflow, self.task_1, self.task_2 = self.create_workflow_and_tasks()

        WorkflowPage.objects.create(workflow=self.workflow, page=self.page)

        self.edit_url = reverse("wagtailadmin_pages:edit", args=(self.page.id,))

    def create_workflow_and_tasks(self):
        workflow = Workflow.objects.create(name="test_workflow")
        task_1 = GroupApprovalTask.objects.create(name="test_task_1")
        task_1.groups.set(Group.objects.filter(name="Moderators"))
        WorkflowTask.objects.create(workflow=workflow, task=task_1, sort_order=1)

        task_2 = GroupApprovalTask.objects.create(name="test_task_2")
        task_2.groups.set(Group.objects.filter(name="Editors"))
        WorkflowTask.objects.create(workflow=workflow, task=task_2, sort_order=2)
        return workflow, task_1, task_2

    def submit(self, action="action-submit"):
        post_data = {
            "title": str(self.page.title),
            "slug": str(self.page.slug),
            "content": str(self.page.content),
            action: "True",
        }
        return self.client.post(self.edit_url, post_data)

    def workflow_action(self, action):
        post_data = {
            "action": action,
            "comment": "good work" if action == "approve" else "needs some changes",
            "next": self.edit_url,
        }
        return self.client.post(
            reverse(
                "wagtailadmin_pages:workflow_action",
                args=(self.page.id, action, self.page.current_workflow_task_state.id),
            ),
            post_data,
            follow=True,
        )

    def test_workflow_status_modal(self):
        workflow_status_url = reverse(
            "wagtailadmin_pages:workflow_status", args=(self.page.id,)
        )

        # The page workflow status view should return permission denied when the page is but a draft
        response = self.client.get(workflow_status_url)
        self.assertRedirects(response, "/admin/")

        # Submit for moderation
        self.submit()

        response = self.client.get(workflow_status_url)
        self.assertEqual(response.status_code, 200)
        html = response.json().get("html")
        self.assertIn(self.task_1.name, html)
        self.assertIn("{}: In progress".format(self.task_1.name), html)
        self.assertIn(self.task_2.name, html)
        self.assertIn("{}: Not started".format(self.task_2.name), html)
        self.assertIn(reverse("wagtailadmin_pages:history", args=(self.page.id,)), html)

        self.assertTemplateUsed(response, "wagtailadmin/workflows/workflow_status.html")

    def test_status_through_workflow_cycle(self):
        self.login(self.superuser)
        response = self.client.get(self.edit_url)
        self.assertContains(response, "Draft", 1)

        self.page.save_revision()
        response = self.client.get(self.edit_url)
        self.assertContains(response, 'id="status-sidebar-draft"')

        self.submit()
        response = self.client.get(self.edit_url)
        self.assertRegex(
            response.content.decode("utf-8"),
            r"Awaiting[\s|\n]+{}".format(self.task_1.name),
        )

        response = self.workflow_action("approve")
        self.assertRegex(
            response.content.decode("utf-8"),
            r"Awaiting[\s|\n]+{}".format(self.task_2.name),
        )

        response = self.workflow_action("reject")
        self.assertContains(response, "Changes requested")

        # resubmit
        self.submit()
        response = self.client.get(self.edit_url)
        self.assertRegex(
            response.content.decode("utf-8"),
            r"Awaiting[\s|\n]+{}".format(self.task_2.name),
        )

        response = self.workflow_action("approve")
        self.assertContains(response, 'id="status-sidebar-live"')

    def test_status_after_cancel(self):
        # start workflow, then cancel
        self.submit()
        self.submit("action-cancel-workflow")
        response = self.client.get(self.edit_url)
        self.assertContains(response, 'id="status-sidebar-draft"')

    def test_status_after_restart(self):
        self.submit()
        response = self.workflow_action("approve")
        self.assertRegex(
            response.content.decode("utf-8"),
            r"Awaiting[\s|\n]+{}".format(self.task_2.name),
        )
        self.workflow_action("reject")
        self.submit("action-restart-workflow")
        response = self.client.get(self.edit_url)
        self.assertRegex(
            response.content.decode("utf-8"),
            r"Awaiting[\s|\n]+{}".format(self.task_1.name),
        )

    def test_workflow_status_modal_task_comments(self):
        workflow_status_url = reverse(
            "wagtailadmin_pages:workflow_status", args=(self.page.id,)
        )

        self.submit()
        self.workflow_action("reject")

        response = self.client.get(workflow_status_url)
        self.assertIn("needs some changes", response.json().get("html"))

        self.submit()
        self.workflow_action("approve")
        response = self.client.get(workflow_status_url)
        self.assertIn("good work", response.json().get("html"))

    def test_workflow_edit_locked_message(self):
        self.submit()
        self.login(self.submitter)
        response = self.client.get(self.edit_url)

        needle = "This page is awaiting <b>'test_task_1'</b> in the <b>'test_workflow'</b> workflow. Only reviewers for this task can edit the page."
        self.assertContains(response, needle)

        self.login(self.moderator)
        response = self.client.get(self.edit_url)
        self.assertNotContains(response, needle)
