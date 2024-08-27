from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

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
        self.christmas_event.save_revision()

        self.site_root = Page.objects.specific().get(id=2)
        self.events_page = self.christmas_event.get_parent().specific

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

        self.assertContains(response, '<div class="w-tabs" data-tabs>')

        self.assertContains(response, '<div class="tab-content">')

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
