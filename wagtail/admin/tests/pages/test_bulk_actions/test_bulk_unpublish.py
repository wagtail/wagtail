from unittest import mock

from django.contrib.auth.models import Permission
from django.http import HttpRequest, HttpResponse
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from wagtail.admin.views.pages.bulk_actions.page_bulk_action import PageBulkAction
from wagtail.models import Page
from wagtail.signals import page_unpublished
from wagtail.test.testapp.models import SimplePage
from wagtail.test.utils import WagtailTestUtils


class TestBulkUnpublish(TestCase, WagtailTestUtils):
    def setUp(self):
        # Create pages to unpublish
        self.root_page = Page.objects.get(id=2)
        self.child_pages = [
            SimplePage(
                title=f"Hello world!-{i}", slug=f"hello-world-{i}", content=f"hello-{i}"
            )
            for i in range(1, 5)
        ]
        # first three child pages will be unpublished
        self.pages_to_be_unpublished = self.child_pages[:3]
        self.pages_not_to_be_unpublished = self.child_pages[3:]
        for child_page in self.child_pages:
            self.root_page.add_child(instance=child_page)

        self.url = (
            reverse(
                "wagtail_bulk_action",
                args=(
                    "wagtailcore",
                    "page",
                    "unpublish",
                ),
            )
            + "?"
        )
        for child_page in self.pages_to_be_unpublished:
            self.url += f"&id={child_page.id}"
        self.redirect_url = reverse("wagtailadmin_explore", args=(self.root_page.id,))

        # Login
        self.user = self.login()

    def test_unpublish_view(self):
        """
        This tests that the unpublish view responds with an unpublish confirm page
        """
        # Request confirm unpublish page
        response = self.client.get(self.url)

        # Check that the user received an unpublish confirm page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/pages/bulk_actions/confirm_bulk_unpublish.html"
        )

    def test_unpublish_view_invalid_page_id(self):
        """
        This tests that the unpublish view returns an error if the page id is invalid
        """
        # Request confirm unpublish page but with illegal page id
        response = self.client.get(
            reverse(
                "wagtail_bulk_action",
                args=(
                    "wagtailcore",
                    "page",
                    "unpublish",
                ),
            )
        )

        # Check that the user received a 404 response
        self.assertEqual(response.status_code, 404)

    def test_unpublish_view_bad_permissions(self):
        """
        This tests that the unpublish view doesn't allow users without unpublish permissions
        """
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        # Request confirm unpublish page
        response = self.client.get(self.url)

        # Check that the user received a 200 redirected response
        self.assertEqual(response.status_code, 200)

        html = response.content.decode()

        self.assertInHTML(
            "<p>You don't have permission to unpublish these pages</p>", html
        )

        for child_page in self.pages_to_be_unpublished:
            self.assertInHTML(
                "<li>{page_title}</li>".format(page_title=child_page.title), html
            )

    def test_unpublish_view_post(self):
        """
        This posts to the unpublish view and checks that the page was unpublished
        """
        # Connect a mock signal handler to page_unpublished signal
        mock_handler = mock.MagicMock()
        page_unpublished.connect(mock_handler)

        # Post to the unpublish page
        response = self.client.post(self.url)

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        # Check that the child pages were unpublished
        for child_page in self.pages_to_be_unpublished:
            self.assertFalse(SimplePage.objects.get(id=child_page.id).live)

        # Check that the child pages not to be unpublished remain
        for child_page in self.pages_not_to_be_unpublished:
            self.assertTrue(SimplePage.objects.get(id=child_page.id).live)

        # Check that the page_unpublished signal was fired
        self.assertEqual(mock_handler.call_count, len(self.pages_to_be_unpublished))

        for i, child_page in enumerate(self.pages_to_be_unpublished):
            mock_call = mock_handler.mock_calls[i][2]
            self.assertEqual(mock_call["sender"], child_page.specific_class)
            self.assertEqual(mock_call["instance"], child_page)
            self.assertIsInstance(mock_call["instance"], child_page.specific_class)

    def test_after_unpublish_page(self):
        def hook_func(request, action_type, pages, action_class_instance):
            self.assertEqual(action_type, "unpublish")
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(action_class_instance, PageBulkAction)
            for i, page in enumerate(pages):
                self.assertEqual(page.id, self.pages_to_be_unpublished[i].id)

            return HttpResponse("Overridden!")

        with self.register_hook("after_bulk_action", hook_func):
            response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        for child_page in self.pages_to_be_unpublished:
            child_page.refresh_from_db()
            self.assertEqual(child_page.status_string, _("draft"))

    def test_before_unpublish_page(self):
        def hook_func(request, action_type, pages, action_class_instance):
            self.assertEqual(action_type, "unpublish")
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(action_class_instance, PageBulkAction)
            for i, page in enumerate(pages):
                self.assertEqual(page.id, self.pages_to_be_unpublished[i].id)

            return HttpResponse("Overridden!")

        with self.register_hook("before_bulk_action", hook_func):
            response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

    def test_unpublish_descendants_view(self):
        """
        This tests that the unpublish view responds with an unpublish confirm page that does not contain the form field 'include_descendants'
        """
        # Get unpublish page for page with no descendants
        response = self.client.get(self.url)

        # Check that the user received an unpublish confirm page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/pages/bulk_actions/confirm_bulk_unpublish.html"
        )
        # Check the form does not contain the checkbox field include_descendants
        self.assertContains(
            response,
            '<input type="checkbox" name="include_descendants" id="id_include_descendants">',
            count=0,
        )


class TestBulkUnpublishIncludingDescendants(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        self.child_pages = [
            SimplePage(
                title=f"Hello world!-{i}", slug=f"hello-world-{i}", content=f"hello-{i}"
            )
            for i in range(1, 5)
        ]
        # first three child pages will be unpublished
        self.pages_to_be_unpublished = self.child_pages[:3]
        self.pages_not_to_be_unpublished = self.child_pages[3:]
        for child_page in self.child_pages:
            self.root_page.add_child(instance=child_page)

        # map of the form { page: [child_pages] } to be added
        self.grandchildren_pages = {
            self.pages_to_be_unpublished[0]: [
                SimplePage(
                    title="Hello world!-a", slug="hello-world-a", content="hello-a"
                )
            ],
            self.pages_to_be_unpublished[1]: [
                SimplePage(
                    title="Hello world!-b", slug="hello-world-b", content="hello-b"
                ),
                SimplePage(
                    title="Hello world!-c", slug="hello-world-c", content="hello-c"
                ),
            ],
        }

        for child_page, grandchild_pages in self.grandchildren_pages.items():
            for grandchild_page in grandchild_pages:
                child_page.add_child(instance=grandchild_page)

        self.url = (
            reverse(
                "wagtail_bulk_action",
                args=(
                    "wagtailcore",
                    "page",
                    "unpublish",
                ),
            )
            + "?"
        )
        for child_page in self.pages_to_be_unpublished:
            self.url += f"&id={child_page.id}"
        self.redirect_url = reverse("wagtailadmin_explore", args=(self.root_page.id,))

        self.user = self.login()

    def test_unpublish_descendants_view(self):
        """
        This tests that the unpublish view responds with an unpublish confirm page that contains the form field 'include_descendants'
        """
        # Get unpublish page
        response = self.client.get(self.url)

        # Check that the user received an unpublish confirm page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/pages/bulk_actions/confirm_bulk_unpublish.html"
        )
        # Check the form contains the checkbox field include_descendants
        self.assertContains(
            response,
            '<input type="checkbox" name="include_descendants" id="id_include_descendants">',
        )

    def test_unpublish_include_children_view_post(self):
        """
        This posts to the unpublish view and checks that the page and its descendants were unpublished
        """
        # Post to the unpublish page
        response = self.client.post(self.url, {"include_descendants": "on"})

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        # Check that the child pages were unpublished
        for child_page in self.pages_to_be_unpublished:
            self.assertFalse(SimplePage.objects.get(id=child_page.id).live)

        # Check that the child pages not to be unpublished remain
        for child_page in self.pages_not_to_be_unpublished:
            self.assertTrue(SimplePage.objects.get(id=child_page.id).live)

        for grandchild_pages in self.grandchildren_pages.values():
            for grandchild_page in grandchild_pages:
                self.assertFalse(SimplePage.objects.get(id=grandchild_page.id).live)

    def test_unpublish_not_include_children_view_post(self):
        """
        This posts to the unpublish view and checks that the page was unpublished but its descendants were not
        """
        # Post to the unpublish page
        response = self.client.post(self.url, {})

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        # Check that the child pages were unpublished
        for child_page in self.pages_to_be_unpublished:
            self.assertFalse(SimplePage.objects.get(id=child_page.id).live)

        # Check that the descendant pages were not unpublished
        for grandchild_pages in self.grandchildren_pages.values():
            for grandchild_page in grandchild_pages:
                self.assertTrue(SimplePage.objects.get(id=grandchild_page.id).live)
