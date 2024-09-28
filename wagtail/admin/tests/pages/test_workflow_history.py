import datetime

from django.conf import settings
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import localize
from freezegun import freeze_time

from wagtail.admin.utils import get_user_display_name
from wagtail.models import Page
from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.template_tests import AdminTemplateTestUtils


class TestWorkflowHistoryDetail(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    fixtures = ["test.json"]
    base_breadcrumb_items = []

    def setUp(self):
        self.user = self.create_test_user()
        self.login(self.user)

        self.christmas_event = Page.objects.get(
            url_path="/home/events/christmas/"
        ).specific

        self.site_root = Page.objects.specific().get(id=2)
        self.events_page = self.christmas_event.get_parent().specific

        workflow = self.christmas_event.get_workflow()

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

        with freeze_time(self.timestamps[0]):
            self.christmas_event.save_revision()
        with freeze_time(self.timestamps[1]):
            self.workflow_state = workflow.start(self.christmas_event, self.user)

    def test_get_index(self):
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:workflow_history", args=[self.christmas_event.id]
            )
        )
        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response, reverse("wagtailadmin_pages:edit", args=[self.christmas_event.id])
        )
        self.assertContains(
            response,
            reverse(
                "wagtailadmin_pages:workflow_history_detail",
                args=[self.christmas_event.id, self.workflow_state.id],
            ),
        )

        # Should show the currently in progress workflow
        self.assertContains(response, "Moderators approval")
        self.assertContains(response, "In progress")
        self.assertContains(response, "test@email.com")

        items = [
            {
                "url": reverse("wagtailadmin_explore_root"),
                "label": "Root",
            },
            {
                "url": reverse("wagtailadmin_explore", args=(self.site_root.id,)),
                "label": self.site_root.get_admin_display_title(),
            },
            {
                "url": reverse("wagtailadmin_explore", args=(self.events_page.id,)),
                "label": self.events_page.get_admin_display_title(),
            },
            {
                "url": reverse("wagtailadmin_explore", args=(self.christmas_event.id,)),
                "label": self.christmas_event.get_admin_display_title(),
            },
            {
                "url": "",
                "label": "Workflow history",
                "sublabel": self.christmas_event.get_admin_display_title(),
            },
        ]
        self.assertBreadcrumbsItemsRendered(items, response.content)

    def test_get_index_with_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.client.get(
            reverse(
                "wagtailadmin_pages:workflow_history", args=[self.christmas_event.id]
            )
        )

        self.assertEqual(response.status_code, 302)

    def test_get_detail(self):
        task_state = self.workflow_state.current_task_state

        with freeze_time(self.timestamps[2]):
            task_state.task.on_action(
                task_state, user=self.moderator, action_name="reject"
            )
        self.workflow_state.refresh_from_db()

        with freeze_time(self.timestamps[3]):
            self.christmas_event.save_revision(user=self.user)
            self.workflow_state.resume(user=self.user)
        self.workflow_state.refresh_from_db()

        url = reverse(
            "wagtailadmin_pages:workflow_history_detail",
            args=[self.christmas_event.id, self.workflow_state.id],
        )
        self.client.get(url)

        with self.assertNumQueries(18):
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response, reverse("wagtailadmin_pages:edit", args=[self.christmas_event.id])
        )
        self.assertContains(
            response,
            reverse(
                "wagtailadmin_pages:workflow_history", args=[self.christmas_event.id]
            ),
        )

        self.assertContains(response, '<div class="w-tabs" data-tabs>')
        self.assertContains(response, '<div class="tab-content">')

        soup = self.get_soup(response.content)
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

        items = [
            {
                "url": reverse("wagtailadmin_explore_root"),
                "label": "Root",
            },
            {
                "url": reverse("wagtailadmin_explore", args=(self.site_root.id,)),
                "label": self.site_root.get_admin_display_title(),
            },
            {
                "url": reverse("wagtailadmin_explore", args=(self.events_page.id,)),
                "label": self.events_page.get_admin_display_title(),
            },
            {
                "url": reverse("wagtailadmin_explore", args=(self.christmas_event.id,)),
                "label": self.christmas_event.get_admin_display_title(),
            },
            {
                "url": reverse(
                    "wagtailadmin_pages:workflow_history",
                    args=(self.christmas_event.id,),
                ),
                "label": "Workflow history",
            },
            {
                "url": "",
                "label": "Workflow progress",
                "sublabel": self.christmas_event.get_admin_display_title(),
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
            self.christmas_event.save_revision(user=self.user)
            self.workflow_state.resume(user=self.user)
        self.workflow_state.refresh_from_db()

        with freeze_time(self.timestamps[4]):
            task_state = self.workflow_state.current_task_state
            task_state.task.on_action(
                task_state, user=self.moderator, action_name="approve"
            )
        self.workflow_state.refresh_from_db()

        url = reverse(
            "wagtailadmin_pages:workflow_history_detail",
            args=[self.christmas_event.id, self.workflow_state.id],
        )
        self.client.get(url)

        with self.assertNumQueries(19):
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response, reverse("wagtailadmin_pages:edit", args=[self.christmas_event.id])
        )
        self.assertContains(
            response,
            reverse(
                "wagtailadmin_pages:workflow_history", args=[self.christmas_event.id]
            ),
        )

        self.assertContains(response, '<div class="w-tabs" data-tabs>')
        self.assertContains(response, '<div class="tab-content">')

        soup = self.get_soup(response.content)
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
            reverse(
                "wagtailadmin_pages:workflow_history_detail",
                args=[self.christmas_event.id, self.workflow_state.id],
            )
        )

        self.assertEqual(response.status_code, 302)
