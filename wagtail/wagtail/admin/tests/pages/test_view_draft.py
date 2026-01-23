from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.models import Page
from wagtail.test.testapp.models import MultiPreviewModesPage, SimplePage, StreamPage
from wagtail.test.utils import WagtailTestUtils


class TestDraftAccess(WagtailTestUtils, TestCase):
    """Tests for the draft view access restrictions."""

    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add child page
        self.child_page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            content="hello",
        )
        self.root_page.add_child(instance=self.child_page)

        # Add stream page (which has empty preview_modes, and so doesn't allow viewing draft)
        self.stream_page = StreamPage(title="stream page", body=[("text", "hello")])
        self.root_page.add_child(instance=self.stream_page)

        # create user with admin access (but not draft_view access)
        user = self.create_user(username="bob", password="password")
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )

    def test_draft_access_admin(self):
        """Test that admin can view draft."""
        # Login as admin
        self.user = self.login()

        # Try getting page draft
        response = self.client.get(
            reverse("wagtailadmin_pages:view_draft", args=(self.child_page.id,))
        )

        # User can view
        self.assertEqual(response.status_code, 200)

    def test_page_without_preview_modes_is_unauthorised(self):
        # Login as admin
        self.user = self.login()

        # Try getting page draft
        response = self.client.get(
            reverse("wagtailadmin_pages:view_draft", args=(self.stream_page.id,))
        )

        # Unauthorised response (because this page type has previewing disabled)
        self.assertRedirects(response, "/admin/")

    def test_draft_access_unauthorised(self):
        """Test that user without edit/publish permission can't view draft."""
        self.login(username="bob", password="password")

        # Try getting page draft
        response = self.client.get(
            reverse("wagtailadmin_pages:view_draft", args=(self.child_page.id,))
        )

        # User gets redirected to the home page
        self.assertEqual(response.status_code, 302)

    def test_draft_access_authorised(self):
        """Test that user with edit permission can view draft."""
        # give user the permission to edit page
        user = get_user_model().objects.get(email="bob@example.com")
        user.groups.add(Group.objects.get(name="Moderators"))
        user.save()

        self.login(username="bob", password="password")

        # Get add subpage page
        response = self.client.get(
            reverse("wagtailadmin_pages:view_draft", args=(self.child_page.id,))
        )

        # User can view
        self.assertEqual(response.status_code, 200)

    def test_middleware_response_is_returned(self):
        """
        If middleware returns a response while serving a page preview, that response should be
        returned back to the user
        """
        self.login()
        response = self.client.get(
            reverse("wagtailadmin_pages:view_draft", args=(self.child_page.id,)),
            HTTP_USER_AGENT="EvilHacker",
        )
        self.assertEqual(response.status_code, 403)

    def test_show_edit_link_in_userbar(self):
        self.login()
        response = self.client.get(
            reverse("wagtailadmin_pages:view_draft", args=(self.child_page.id,))
        )
        # Should show edit link in the userbar
        # https://github.com/wagtail/wagtail/issues/10002
        self.assertContains(response, "Edit this page")
        self.assertContains(
            response, reverse("wagtailadmin_pages:edit", args=(self.child_page.id,))
        )

    def test_preview_modes(self):
        """
        Test that the preview_modes are respected when viewing a draft.
        """
        # Create a page with multiple preview modes
        page = MultiPreviewModesPage(title="multi preview modes page")
        self.root_page.add_child(instance=page)

        # Login as admin
        self.user = self.login()

        # Test using explicit preview mode parameter
        for mode, label in page.preview_modes:
            with self.subTest(mode=mode, label=label):
                response = self.client.get(
                    reverse("wagtailadmin_pages:view_draft", args=(page.id,)),
                    {"mode": mode},
                )
                # Ensure the correct template is used
                self.assertEqual(response.status_code, 200)
                preview_template = page.preview_templates[mode]
                self.assertTemplateUsed(response, preview_template)

        # Test default preview mode with no parameter
        response = self.client.get(
            reverse("wagtailadmin_pages:view_draft", args=(page.id,)),
        )
        self.assertEqual(response.status_code, 200)
        preview_template = page.preview_templates[page.default_preview_mode]
        self.assertTemplateUsed(response, preview_template)
