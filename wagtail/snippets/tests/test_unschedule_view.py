import datetime

from django.contrib.admin.utils import quote
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now

from wagtail.models import Revision
from wagtail.test.testapp.models import DraftStateCustomPrimaryKeyModel
from wagtail.test.utils import WagtailTestUtils


class TestSnippetUnschedule(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()
        self.test_snippet = DraftStateCustomPrimaryKeyModel.objects.create(
            custom_id="custom/1", text="Draft-enabled Foo", live=False
        )
        self.go_live_at = now() + datetime.timedelta(days=1)
        self.test_snippet.text = "I've been edited!"
        self.test_snippet.go_live_at = self.go_live_at
        self.latest_revision = self.test_snippet.save_revision()
        self.latest_revision.publish()
        self.test_snippet.refresh_from_db()
        self.unschedule_url = reverse(
            "wagtailsnippets_tests_draftstatecustomprimarykeymodel:revisions_unschedule",
            args=[quote(self.test_snippet.pk), self.latest_revision.pk],
        )

    def set_permissions(self, set_publish_permission):
        self.user.is_superuser = False

        permissions = [
            Permission.objects.get(
                content_type__app_label="tests",
                codename="change_draftstatecustomprimarykeymodel",
            ),
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            ),
        ]

        if set_publish_permission:
            permissions.append(
                Permission.objects.get(
                    content_type__app_label="tests",
                    codename="publish_draftstatecustomprimarykeymodel",
                )
            )

        self.user.user_permissions.add(*permissions)
        self.user.save()

    def test_get_unschedule_view_with_publish_permissions(self):
        self.set_permissions(True)

        # Get unschedule page
        response = self.client.get(self.unschedule_url)

        # Check that the user received a confirmation page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/shared/revisions/confirm_unschedule.html"
        )

    def test_get_unschedule_view_bad_permissions(self):
        self.set_permissions(False)

        # Get unschedule page
        response = self.client.get(self.unschedule_url)

        # Check that the user is redirected to the admin homepage
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_post_unschedule_view_with_publish_permissions(self):
        self.set_permissions(True)

        # Post unschedule page
        response = self.client.post(self.unschedule_url)

        # Check that the user was redirected to the history page
        self.assertRedirects(
            response,
            reverse(
                "wagtailsnippets_tests_draftstatecustomprimarykeymodel:history",
                args=[quote(self.test_snippet.pk)],
            ),
        )

        self.test_snippet.refresh_from_db()
        self.latest_revision.refresh_from_db()

        # Check that the revision is no longer scheduled
        self.assertIsNone(self.latest_revision.approved_go_live_at)

        # No revisions with approved_go_live_at
        self.assertFalse(
            Revision.objects.for_instance(self.test_snippet)
            .exclude(approved_go_live_at__isnull=True)
            .exists()
        )

    def test_post_unschedule_view_bad_permissions(self):
        self.set_permissions(False)

        # Post unschedule page
        response = self.client.post(self.unschedule_url)

        # Check that the user is redirected to the admin homepage
        self.assertRedirects(response, reverse("wagtailadmin_home"))

        self.test_snippet.refresh_from_db()
        self.latest_revision.refresh_from_db()

        # Check that the revision is still scheduled
        self.assertIsNotNone(self.latest_revision.approved_go_live_at)

        # Revision with approved_go_live_at exists
        self.assertTrue(
            Revision.objects.for_instance(self.test_snippet)
            .exclude(approved_go_live_at__isnull=True)
            .exists()
        )

    def test_post_unschedule_view_with_next_url(self):
        self.set_permissions(True)

        edit_url = reverse(
            "wagtailsnippets_tests_draftstatecustomprimarykeymodel:edit",
            args=[quote(self.test_snippet.pk)],
        )

        # Post unschedule page
        response = self.client.post(self.unschedule_url + f"?next={edit_url}")

        # Check that the user was redirected to the next url
        self.assertRedirects(response, edit_url)

        self.test_snippet.refresh_from_db()
        self.latest_revision.refresh_from_db()

        # Check that the revision is no longer scheduled
        self.assertIsNone(self.latest_revision.approved_go_live_at)

        # No revisions with approved_go_live_at
        self.assertFalse(
            Revision.objects.for_instance(self.test_snippet)
            .exclude(approved_go_live_at__isnull=True)
            .exists()
        )
