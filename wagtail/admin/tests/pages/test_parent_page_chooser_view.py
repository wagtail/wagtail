from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.models import GroupPagePermission, Page
from wagtail.test.testapp.models import BusinessIndex
from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.template_tests import AdminTemplateTestUtils


class TestParentPageChooserView(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        super().setUp()
        self.user = self.login()
        self.view_url = reverse("event_pages:choose_parent")

    def test_get_page_parent_chooser(self):
        response = self.client.get(self.view_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/choose_parent.html")
        self.assertBreadcrumbsItemsRendered(
            [
                {"url": reverse("event_pages:index"), "label": "Event pages"},
                {"url": "", "label": "Choose parent", "sublabel": "Event page"},
            ],
            response.content,
        )

    def test_parent_chooser_redirect(self):
        parent_page = Page.objects.first()
        form_data = {
            "parent_page": parent_page.pk,
        }

        response = self.client.post(self.view_url, form_data)
        self.assertRedirects(
            response,
            reverse(
                "wagtailadmin_pages:add", args=("tests", "eventpage", parent_page.pk)
            ),
        )

        # Test another parent to make sure everything is working as intended
        another_parent = parent_page.get_first_child()
        form_data["parent_page"] = another_parent.pk

        response = self.client.post(self.view_url, form_data)
        self.assertRedirects(
            response,
            reverse(
                "wagtailadmin_pages:add", args=("tests", "eventpage", another_parent.pk)
            ),
        )

    def test_no_parent_selected(self):
        error_html = """<p class="error-message">This field is required.</p>"""

        response = self.client.post(self.view_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, error_html, html=True)

    def test_user_no_add_subpage_permission(self):
        parent_page = Page.objects.first()
        test_group = Group.objects.create(name="test_group")
        test_group.permissions.add(Permission.objects.get(codename="access_admin"))

        page_with_add_permission = Page(title="Page not to be selected")
        page_with_no_permission = Page(title="Page to be selected")
        parent_page.add_child(instance=page_with_add_permission)
        parent_page.add_child(instance=page_with_no_permission)

        GroupPagePermission.objects.create(
            group=test_group,
            page=page_with_add_permission,
            permission_type="add",
        )
        form_data = {
            "parent_page": page_with_no_permission.pk,
        }

        self.user.is_superuser = False
        self.user.groups.add(test_group)
        self.user.save()

        response = self.client.post(self.view_url, form_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            " You do not have permission to create a page under &quot;%s&quot;. "
            % page_with_no_permission.get_admin_display_title(),
        )

        form_data["parent_page"] = page_with_add_permission.pk
        response = self.client.post(self.view_url, form_data)
        self.assertRedirects(
            response,
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "eventpage", page_with_add_permission.pk),
            ),
        )

    def test_choosing_parent_with_unsupported_subpage_type(self):
        parent_page = Page.objects.first()
        page_with_limited_subtypes = BusinessIndex(title="EventPage unsupported")
        parent_page.add_child(instance=page_with_limited_subtypes)
        form_data = {
            "parent_page": page_with_limited_subtypes.pk,
        }

        response = self.client.post(self.view_url, form_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "You cannot create a page of type &quot;Event page&quot; under &quot;%s&quot;."
            % page_with_limited_subtypes.get_admin_display_title(),
        )
