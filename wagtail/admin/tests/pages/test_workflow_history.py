from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.models import Page
from wagtail.test.utils import WagtailTestUtils


class TestWorkflowHistoryDetail(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        self.user = self.create_test_user()
        self.login(self.user)

        self.christmas_event = Page.objects.get(url_path="/home/events/christmas/")
        self.christmas_event.save_revision()

        workflow = self.christmas_event.get_workflow()
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
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:workflow_history_detail",
                args=[self.christmas_event.id, self.workflow_state.id],
            )
        )
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
