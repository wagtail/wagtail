import datetime

from django.conf import settings
from django.contrib.admin.utils import quote
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import localize
from freezegun import freeze_time

from wagtail.admin.utils import get_user_display_name
from wagtail.models import Workflow, WorkflowContentType, WorkflowState
from wagtail.test.testapp.models import FullFeaturedSnippet, ModeratedModel
from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.template_tests import AdminTemplateTestUtils

# This module serves to gather snippets-equivalent of workflows-related tests
# that are found throughout page-specific test modules, e.g. test_create_page.py,
# test_edit_page.py, etc.
# The main workflows test modules contain tests for both pages and snippets
# and can be found in:
#   - wagtail.tests.test_workflow
#     for testing workflow operations through the Workflow model methods
#   - wagtail.admin.tests.test_workflows
#     for testing workflow operations through views and testing Workflow settings views


class BaseWorkflowsTestCase(WagtailTestUtils, TestCase):
    model = FullFeaturedSnippet

    def setUp(self):
        self.user = self.login()
        self.object = self.model.objects.create(text="I'm a full-featured snippet!")
        self.object.save_revision().publish()

        # Assign default workflow to the snippet model
        self.content_type = ContentType.objects.get_for_model(self.model)
        self.workflow = Workflow.objects.first()
        WorkflowContentType.objects.create(
            content_type=self.content_type,
            workflow=self.workflow,
        )

    @property
    def model_name(self):
        return self.model._meta.verbose_name

    def get_url(self, name, args=None):
        args = args if args is not None else [quote(self.object.pk)]
        return reverse(self.object.snippet_viewset.get_url_name(name), args=args)


class TestCreateView(BaseWorkflowsTestCase):
    def get(self):
        return self.client.get(self.get_url("add", ()))

    def post(self, post_data):
        return self.client.post(self.get_url("add", ()), post_data)

    def test_get_workflow_buttons_shown(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<button type="submit" name="action-submit" value="Submit to Moderators approval" class="button">',
            count=1,
        )

    @override_settings(WAGTAIL_WORKFLOW_ENABLED=False)
    def test_get_workflow_buttons_not_shown_when_workflow_disabled(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="action-submit"')

    def test_post_submit_for_moderation(self):
        response = self.post({"text": "Newly created", "action-submit": "Submit"})
        object = self.model.objects.get(text="Newly created")

        self.assertRedirects(response, self.get_url("list", ()))
        self.assertIsInstance(object, self.model)

        # The object should be created, but not live
        self.assertEqual(object.text, "Newly created")
        self.assertFalse(object.live)
        self.assertFalse(object.first_published_at)

        # The object should now be in moderation
        self.assertEqual(
            object.current_workflow_state.status,
            WorkflowState.STATUS_IN_PROGRESS,
        )

        # There should be a draft revision with the data
        self.assertEqual(object.latest_revision.object_str, "Newly created")

        # The current task state should point to the latest revision
        self.assertEqual(
            object.current_workflow_task_state.revision,
            object.latest_revision,
        )


class TestCreateViewNotLockable(TestCreateView):
    model = ModeratedModel


class TestEditView(BaseWorkflowsTestCase):
    def get(self):
        return self.client.get(self.get_url("edit"))

    def post(self, post_data):
        return self.client.post(self.get_url("edit"), post_data)

    def test_get_workflow_buttons_shown(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<button type="submit" name="action-submit" value="Submit to Moderators approval" class="button">',
            count=1,
        )

    @override_settings(WAGTAIL_WORKFLOW_ENABLED=False)
    def test_get_workflow_buttons_not_shown_when_workflow_disabled(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="action-submit"')

    def test_post_submit_for_moderation(self):
        response = self.post({"text": "Edited!", "action-submit": "Submit"})
        self.object.refresh_from_db()

        self.assertRedirects(response, self.get_url("list", ()))
        self.assertIsInstance(self.object, self.model)

        # The live instance should still be live and should not be updated
        self.assertEqual(self.object.text, "I'm a full-featured snippet!")
        self.assertTrue(self.object.live)
        self.assertTrue(self.object.first_published_at)
        self.assertTrue(self.object.has_unpublished_changes)

        # The object should now be in moderation
        self.assertEqual(
            self.object.current_workflow_state.status,
            WorkflowState.STATUS_IN_PROGRESS,
        )

        # There should be a draft revision with the changes
        self.assertEqual(self.object.latest_revision.object_str, "Edited!")

        # The current task state should point to the latest revision
        self.assertEqual(
            self.object.current_workflow_task_state.revision,
            self.object.latest_revision,
        )


class TestEditViewNotLockable(TestEditView):
    model = ModeratedModel


class TestWorkflowHistory(AdminTemplateTestUtils, BaseWorkflowsTestCase):
    def setUp(self):
        super().setUp()
        self.timestamps = [
            datetime.datetime(2020, 1, 1, 10, 0, 0),
            datetime.datetime(2020, 1, 1, 11, 0, 0),
            datetime.datetime(2020, 1, 2, 12, 0, 0),
            datetime.datetime(2020, 1, 3, 13, 0, 0),
            datetime.datetime(2020, 1, 4, 14, 0, 0),
        ]

        if settings.USE_TZ:
            self.timestamps[:] = [
                timezone.make_aware(timestamp, timezone=datetime.timezone.utc)
                for timestamp in self.timestamps
            ]
            self.localized_timestamps = [
                localize(timezone.localtime(timestamp), "c")
                for timestamp in self.timestamps
            ]
        else:
            self.localized_timestamps = [
                localize(timestamp, "c") for timestamp in self.timestamps
            ]

        self.moderator = self.create_superuser("moderator")
        self.moderator_name = get_user_display_name(self.moderator)
        self.user_name = get_user_display_name(self.user)

        self.object.text = "Edited!"
        with freeze_time(self.timestamps[0]):
            self.object.save_revision()
        with freeze_time(self.timestamps[1]):
            self.workflow_state = self.workflow.start(self.object, self.user)

    def test_get_index(self):
        response = self.client.get(self.get_url("workflow_history"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/shared/workflow_history/listing.html"
        )

        self.assertContains(response, self.get_url("edit"))
        self.assertContains(
            response,
            self.get_url(
                "workflow_history_detail",
                (quote(self.object.pk), self.workflow_state.id),
            ),
        )

        # Should show the currently in progress workflow
        self.assertContains(response, "Moderators approval")
        self.assertContains(response, "In progress")
        self.assertContains(response, "test@email.com")

    def test_get_index_with_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.client.get(self.get_url("workflow_history"))

        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_get_detail(self):
        task_state = self.workflow_state.current_task_state

        with freeze_time(self.timestamps[2]):
            task_state.task.on_action(
                task_state, user=self.moderator, action_name="reject"
            )
        self.workflow_state.refresh_from_db()

        with freeze_time(self.timestamps[3]):
            self.object.save_revision(user=self.user)
            self.workflow_state.resume(user=self.user)
        self.workflow_state.refresh_from_db()

        url = self.get_url(
            "workflow_history_detail",
            (quote(self.object.pk), self.workflow_state.id),
        )
        self.client.get(url)

        with self.assertNumQueries(18):
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/shared/workflow_history/detail.html"
        )

        self.assertContains(response, self.get_url("edit"))
        self.assertContains(response, self.get_url("workflow_history"))

        soup = self.get_soup(response.content)

        self.assertIsNotNone(soup.select_one('[data-controller~="w-tabs"]'))
        self.assertIsNotNone(soup.select_one(".tab-content"))

        tasks = soup.select_one("#tab-tasks table")
        self.assertIsNotNone(tasks)
        cells = [
            [td.get_text(separator=" ", strip=True) for td in tr.select("td")]
            for tr in tasks.select("tr")
        ]

        self.assertEqual(
            cells,
            [
                # This is divided into different columns per task, so it makes
                # sense to start with the initial revision on the first cell and
                # then it should be rendered in ascending order.
                [
                    "Initial Revision",
                    f"Rejected by {self.moderator_name} at {self.localized_timestamps[2]}",
                ],
                [
                    f"Edited by {self.user_name} at {self.localized_timestamps[3]}",
                    "In progress",
                ],
            ],
        )

        timeline = soup.select_one("#tab-timeline table")
        self.assertIsNotNone(timeline)
        cells = [
            [td.get_text(separator=" ", strip=True) for td in tr.select("td")]
            for tr in timeline.select("tr")
        ]
        self.assertEqual(
            cells,
            [
                # The items are merged into a single column as a timeline, so it
                # should be rendered in reverse chronological order.
                [
                    self.localized_timestamps[3],
                    "Edited",
                ],
                [
                    self.localized_timestamps[2],
                    f"Moderators approval Rejected by {self.moderator_name}",
                ],
                [
                    self.localized_timestamps[1],
                    "Workflow started",
                ],
                [
                    self.localized_timestamps[0],
                    "Edited",
                ],
            ],
        )

        # Should show the currently in progress workflow with the latest revision
        self.assertContains(response, "Edited!")
        self.assertContains(response, "Moderators approval")
        self.assertContains(response, "In progress")
        self.assertContains(response, "test@email.com")

        items = [
            {
                "url": self.get_url("list", args=()),
                "label": "Full-featured snippets",
            },
            {
                "url": self.get_url("edit"),
                "label": str(self.object),
            },
            {
                "url": self.get_url("workflow_history"),
                "label": "Workflow history",
            },
            {
                "url": "",
                "label": "Workflow progress",
                "sublabel": str(self.object),
            },
        ]
        self.assertBreadcrumbsItemsRendered(items, response.content)

    def test_get_detail_completed(self):
        task_state = self.workflow_state.current_task_state

        with freeze_time(self.timestamps[2]):
            task_state.task.on_action(
                task_state, user=self.moderator, action_name="reject"
            )
        self.workflow_state.refresh_from_db()

        with freeze_time(self.timestamps[3]):
            self.object.save_revision(user=self.user)
            self.workflow_state.resume(user=self.user)
        self.workflow_state.refresh_from_db()

        with freeze_time(self.timestamps[4]):
            task_state = self.workflow_state.current_task_state
            task_state.task.on_action(
                task_state, user=self.moderator, action_name="approve"
            )
        self.workflow_state.refresh_from_db()

        url = self.get_url(
            "workflow_history_detail",
            (quote(self.object.pk), self.workflow_state.id),
        )
        self.client.get(url)

        with self.assertNumQueries(19):
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/shared/workflow_history/detail.html"
        )

        self.assertContains(response, self.get_url("edit"))
        self.assertContains(response, self.get_url("workflow_history"))

        soup = self.get_soup(response.content)

        self.assertIsNotNone(soup.select_one('[data-controller~="w-tabs"]'))
        self.assertIsNotNone(soup.select_one(".tab-content"))

        tasks = soup.select_one("#tab-tasks table")
        self.assertIsNotNone(tasks)
        cells = [
            [td.get_text(separator=" ", strip=True) for td in tr.select("td")]
            for tr in tasks.select("tr")
        ]

        self.assertEqual(
            cells,
            [
                # This is divided into different columns per task, so it makes
                # sense to start with the initial revision on the first cell and
                # then it should be rendered in ascending order.
                [
                    "Initial Revision",
                    f"Rejected by {self.moderator_name} at {self.localized_timestamps[2]}",
                ],
                [
                    f"Edited by {self.user_name} at {self.localized_timestamps[3]}",
                    f"Approved by {self.moderator_name} at {self.localized_timestamps[4]}",
                ],
            ],
        )

        timeline = soup.select_one("#tab-timeline table")
        self.assertIsNotNone(timeline)
        cells = [
            [td.get_text(separator=" ", strip=True) for td in tr.select("td")]
            for tr in timeline.select("tr")
        ]
        self.assertEqual(
            cells,
            [
                # The items are merged into a single column as a timeline, so it
                # should be rendered in reverse chronological order.
                [
                    self.localized_timestamps[4],
                    "Workflow completed Approved",
                ],
                [
                    self.localized_timestamps[4],
                    f"Moderators approval Approved by {self.moderator_name}",
                ],
                [
                    self.localized_timestamps[3],
                    "Edited",
                ],
                [
                    self.localized_timestamps[2],
                    f"Moderators approval Rejected by {self.moderator_name}",
                ],
                [
                    self.localized_timestamps[1],
                    "Workflow started",
                ],
                [
                    self.localized_timestamps[0],
                    "Edited",
                ],
            ],
        )

        # Should show the completed workflow with the latest revision
        self.assertContains(response, "Edited!")
        self.assertContains(response, "Moderators approval")
        self.assertContains(response, "Workflow completed")
        self.assertContains(response, "test@email.com")
        self.assertNotContains(response, "In progress")

    def test_get_detail_with_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.client.get(
            self.get_url(
                "workflow_history_detail",
                (quote(self.object.pk), self.workflow_state.id),
            ),
        )

        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_get_history_renders_comment(self):
        self.workflow_state.current_task_state.reject(comment="Can be better")
        # Ensure the comment in the log entry is rendered in the History view.
        # This is the main History view and not the Workflow History view, but
        # we test it here so we can reuse the workflow setup.
        response = self.client.get(self.get_url("history", (quote(self.object.pk),)))
        self.assertContains(
            response,
            "<div>Comment: <em>Can be better</em></div>",
            html=True,
        )


class TestConfirmWorkflowCancellation(BaseWorkflowsTestCase):
    def setUp(self):
        super().setUp()
        self.object.text = "Edited!"
        self.object.save_revision()
        self.workflow_state = self.workflow.start(self.object, self.user)

    def test_get_confirm_workflow_cancellation(self):
        response = self.client.get(self.get_url("confirm_workflow_cancellation"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/generic/confirm_workflow_cancellation.html"
        )
        self.assertContains(
            response,
            "Publishing this full-featured snippet will cancel the current workflow.",
        )
        self.assertContains(
            response, "Would you still like to publish this full-featured snippet?"
        )

    @override_settings(WAGTAIL_WORKFLOW_CANCEL_ON_PUBLISH=False)
    def test_get_confirm_workflow_cancellation_with_disabled_setting(self):
        response = self.client.get(self.get_url("confirm_workflow_cancellation"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateNotUsed(
            response,
            "wagtailadmin/generic/confirm_workflow_cancellation.html",
        )
        self.assertJSONEqual(
            response.content.decode(),
            {"step": "no_confirmation_needed"},
        )
