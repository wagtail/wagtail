from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse
from django.utils.http import urlencode

from wagtail.models import GroupPagePermission, Page
from wagtail.test.testapp.models import EventPage
from wagtail.test.utils import WagtailTestUtils


class TestContentTypeUse(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.user = self.login()
        self.christmas_page = EventPage.objects.get(title="Christmas")

    def test_with_no_permission(self):
        request_url = reverse(
            "wagtailadmin_pages:type_use", args=("tests", "eventpage")
        )
        group = Group.objects.create(name="test group")
        self.user.is_superuser = False
        self.user.save()
        self.user.groups.add(group)
        group.permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        # No GroupPagePermission created

        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_with_minimal_permissions(self):
        request_url = reverse(
            "wagtailadmin_pages:type_use", args=("tests", "eventpage")
        )
        group = Group.objects.create(name="test group")
        self.user.is_superuser = False
        self.user.save()
        self.user.groups.add(group)
        group.permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            ),
        )
        GroupPagePermission.objects.create(
            group=group,
            page=Page.objects.first(),
            permission_type="change",
        )

        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)

    def test_content_type_use(self):
        # Get use of event page
        request_url = reverse(
            "wagtailadmin_pages:type_use", args=("tests", "eventpage")
        )
        response = self.client.get(request_url)

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/listing.html")
        self.assertTemplateUsed(response, "wagtailadmin/generic/listing_results.html")
        self.assertContains(response, "Christmas")

        # Links to 'delete' etc should include a 'next' URL parameter pointing back here
        delete_url = (
            reverse("wagtailadmin_pages:delete", args=(self.christmas_page.id,))
            + "?"
            + urlencode({"next": request_url})
        )
        self.assertContains(response, delete_url)
        self.assertContains(response, "data-bulk-action-select-all-checkbox")

        with self.assertNumQueries(33):
            self.client.get(request_url)

    def test_content_type_use_results(self):
        # Get the results view of event page use, with search and filter
        ameristralia_page = EventPage.objects.get(title="Ameristralia Day")
        user = get_user_model().objects.get(email="eventmoderator@example.com")
        request_url = reverse(
            "wagtailadmin_pages:type_use_results",
            args=("tests", "eventpage"),
        )
        response = self.client.get(
            request_url,
            data={"q": "Ameristralia", "owner": user.pk},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateNotUsed(response, "wagtailadmin/generic/listing.html")
        self.assertTemplateUsed(response, "wagtailadmin/generic/listing_results.html")
        self.assertContains(response, "Ameristralia Day")

        # Links to 'delete' etc should include a 'next' URL parameter pointing back
        # to the full view, not the results-only view
        full_view_url = reverse(
            "wagtailadmin_pages:type_use",
            args=("tests", "eventpage"),
        )
        delete_url = (
            reverse("wagtailadmin_pages:delete", args=(ameristralia_page.id,))
            + "?"
            + urlencode({"next": full_view_url})
        )
        self.assertContains(response, delete_url)
        self.assertContains(response, "data-bulk-action-select-all-checkbox")
