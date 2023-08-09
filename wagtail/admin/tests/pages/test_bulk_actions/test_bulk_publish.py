from unittest import mock

from django.contrib.auth.models import Permission
from django.http import HttpRequest, HttpResponse
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from wagtail.admin.views.pages.bulk_actions.page_bulk_action import PageBulkAction
from wagtail.models import Page
from wagtail.signals import page_published
from wagtail.test.testapp.models import SimplePage
from wagtail.test.utils import WagtailTestUtils


class TestBulkPublish(WagtailTestUtils, TestCase):
    def setUp(self):
        self.root_page = Page.objects.get(id=2)

        # Add child pages which will have already been published before we
        # bulk publish them.
        self.child_pages = [
            SimplePage(
                title=f"Hello world!-{i}",
                slug=f"hello-world-{i}",
                content=f"Hello world {i}!",
                live=False,
            )
            for i in range(1, 5)
        ]

        self.pages_to_be_published = self.child_pages[:3]
        self.pages_not_to_be_published = self.child_pages[3:]

        for child_page in self.child_pages:
            self.root_page.add_child(instance=child_page)

        for i, child_page in enumerate(self.child_pages):
            child_page.content = f"Hello published world {i}!"
            child_page.save_revision()

        # Add an additional child page which will be bulk published from a
        # draft-only state.
        draft_page = SimplePage(
            title="Hello world!-5",
            slug="hello-world-5",
            content="Hello published world 5!",
            live=False,
        )

        self.root_page.add_child(instance=draft_page)
        self.child_pages.append(draft_page)
        self.pages_to_be_published.append(draft_page)

        self.url = (
            reverse(
                "wagtail_bulk_action",
                args=(
                    "wagtailcore",
                    "page",
                    "publish",
                ),
            )
            + "?"
        )
        for child_page in self.pages_to_be_published:
            self.url += f"id={child_page.id}&"
        self.redirect_url = reverse("wagtailadmin_explore", args=(self.root_page.id,))

        self.user = self.login()

    def test_publish_view(self):
        """
        This tests that the publish view responds with an publish confirm page
        """
        # Request confirm publish page
        response = self.client.get(self.url)

        # # Check that the user received an publish confirm page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/pages/bulk_actions/confirm_bulk_publish.html"
        )

        # Page titles shown on the confirmation page should use SimplePage's custom get_admin_display_title method
        self.assertContains(response, "Hello world!-1 (simple page)")

    def test_publish_view_invalid_page_id(self):
        """
        This tests that the publish view returns an error if the page id is invalid
        """
        # Request confirm publish page but with illegal page id
        response = self.client.get(
            reverse(
                "wagtail_bulk_action",
                args=(
                    "wagtailcore",
                    "page",
                    "publish",
                ),
            )
        )

        # Check that the user received a 404 response
        self.assertEqual(response.status_code, 404)

    def test_publish_view_bad_permissions(self):
        """
        This tests that the publish view doesn't allow users without publish permissions
        """
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        # Request confirm publish page
        response = self.client.get(self.url)

        # Check that the user received a 200 redirected response
        self.assertEqual(response.status_code, 200)

        html = response.content.decode()

        self.assertInHTML(
            "<p>You don't have permission to publish these pages</p>", html
        )

        for child_page in self.pages_to_be_published:
            self.assertInHTML(f"<li>{child_page.title}</li>", html)

    def test_publish_view_post(self):
        """
        This posts to the publish view and checks that the page was published
        """
        # Connect a mock signal handler to page_published signal
        mock_handler = mock.MagicMock()
        page_published.connect(mock_handler)

        try:
            # Post to the publish page
            response = self.client.post(self.url)

            # Should be redirected to explorer page
            self.assertEqual(response.status_code, 302)

            # Check that the child pages were published
            for child_page in self.pages_to_be_published:
                published_page = SimplePage.objects.get(id=child_page.id)
                self.assertTrue(published_page.live)
                self.assertIn("Hello published", published_page.content)

            # Check that the child pages not to be published remain
            for child_page in self.pages_not_to_be_published:
                self.assertFalse(Page.objects.get(id=child_page.id).live)

            # Check that the page_published signal was fired
            self.assertEqual(mock_handler.call_count, len(self.pages_to_be_published))

            for i, child_page in enumerate(self.pages_to_be_published):
                mock_call = mock_handler.mock_calls[i][2]
                self.assertEqual(mock_call["sender"], child_page.specific_class)
                self.assertEqual(mock_call["instance"], child_page)
                self.assertIsInstance(mock_call["instance"], child_page.specific_class)
        finally:
            page_published.disconnect(mock_handler)

    def test_after_publish_page(self):
        def hook_func(request, action_type, pages, action_class_instance):
            self.assertEqual(action_type, "publish")
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(action_class_instance, PageBulkAction)
            for i, page in enumerate(pages):
                self.assertEqual(page.id, self.pages_to_be_published[i].id)

            return HttpResponse("Overridden!")

        with self.register_hook("after_bulk_action", hook_func):
            response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        for child_page in self.pages_to_be_published:
            child_page.refresh_from_db()
            self.assertEqual(child_page.status_string, _("live"))

    def test_before_publish_page(self):
        def hook_func(request, action_type, pages, action_class_instance):
            self.assertEqual(action_type, "publish")
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(action_class_instance, PageBulkAction)
            for i, page in enumerate(pages):
                self.assertEqual(page.id, self.pages_to_be_published[i].id)

            return HttpResponse("Overridden!")

        with self.register_hook("before_bulk_action", hook_func):
            response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

    def test_publish_descendants_view(self):
        """
        This tests that the publish view responds with an publish confirm page that does not contain the form field 'include_descendants'
        """
        # Get publish page for page with no descendants
        response = self.client.get(self.url)

        # Check that the user received an publish confirm page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/pages/bulk_actions/confirm_bulk_publish.html"
        )
        # Check the form does not contain the checkbox field include_descendants
        self.assertNotContains(
            response,
            'name="include_descendants"',
        )


class TestBulkPublishIncludingDescendants(WagtailTestUtils, TestCase):
    def setUp(self):
        self.root_page = Page.objects.get(id=2)

        # Add child pages
        self.child_pages = [
            SimplePage(
                title=f"Hello world!-{i}",
                slug=f"hello-world-{i}",
                content=f"Hello world {i}!",
                live=False,
            )
            for i in range(1, 5)
        ]
        self.pages_to_be_published = self.child_pages[:3]
        self.pages_not_to_be_published = self.child_pages[3:]

        for child_page in self.child_pages:
            self.root_page.add_child(instance=child_page)

        for i, child_page in enumerate(self.child_pages):
            child_page.content = f"Hello updated world {i}!"
            child_page.save_revision()

        # Add grandchild pages which will have already been published before
        # we bulk publish them.
        # map of the form { page: [child_pages] } to be added
        self.grandchildren_pages = {
            self.pages_to_be_published[0]: [
                SimplePage(
                    title="Hello world!-a",
                    slug="hello-world-a",
                    content="Hello world a!",
                    live=False,
                )
            ],
            self.pages_to_be_published[1]: [
                SimplePage(
                    title="Hello world!-b",
                    slug="hello-world-b",
                    content="Hello world b!",
                    live=False,
                ),
                SimplePage(
                    title="Hello world!-c",
                    slug="hello-world-c",
                    content="Hello world c!",
                    live=False,
                ),
            ],
        }
        for child_page, grandchild_pages in self.grandchildren_pages.items():
            for grandchild_page in grandchild_pages:
                child_page.add_child(instance=grandchild_page)

        for child_page, grandchild_pages in self.grandchildren_pages.items():
            for grandchild_page in grandchild_pages:
                grandchild_page.content = grandchild_page.content.replace(
                    "Hello world", "Hello grandchild"
                )
                grandchild_page.save_revision()

        # Add an additional grandchild page which will be bulk published from
        # a draft-only state.
        draft_page = SimplePage(
            title="Hello world!-d",
            slug="hello-world-d",
            content="Hello grandchild d!",
            live=False,
        )

        self.pages_to_be_published[1].add_child(instance=draft_page)
        self.grandchildren_pages[self.pages_to_be_published[1]].append(draft_page)

        self.url = (
            reverse(
                "wagtail_bulk_action",
                args=(
                    "wagtailcore",
                    "page",
                    "publish",
                ),
            )
            + "?"
        )
        for child_page in self.pages_to_be_published:
            self.url += f"&id={child_page.id}"

        self.user = self.login()

    def test_publish_descendants_view(self):
        """
        This tests that the publish view responds with an publish confirm page that contains the form field 'include_descendants'
        """
        # Get publish page
        response = self.client.get(self.url)

        # Check that the user received an publish confirm page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/pages/bulk_actions/confirm_bulk_publish.html"
        )
        # Check the form contains the checkbox field include_descendants
        self.assertContains(
            response,
            'name="include_descendants"',
        )

    def test_publish_include_children_view_post(self):
        """
        This posts to the publish view and checks that the page and its descendants were published
        """
        # Post to the publish page
        response = self.client.post(self.url, {"include_descendants": "on"})

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        # Check that the child pages were published
        for child_page in self.pages_to_be_published:
            published_child_page = SimplePage.objects.get(id=child_page.id)
            self.assertTrue(published_child_page.live)
            self.assertIn("Hello updated", published_child_page.content)

        # Check that the child pages not to be published remain
        for child_page in self.pages_not_to_be_published:
            self.assertFalse(Page.objects.get(id=child_page.id).live)

        for grandchild_pages in self.grandchildren_pages.values():
            for grandchild_page in grandchild_pages:
                published_grandchild_page = SimplePage.objects.get(
                    id=grandchild_page.id
                )
                self.assertTrue(published_grandchild_page.live)
                self.assertIn("Hello grandchild", published_grandchild_page.content)

    def test_publish_not_include_children_view_post(self):
        """
        This posts to the publish view and checks that the page was published but its descendants were not
        """
        # Post to the publish page
        response = self.client.post(self.url, {})

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        # Check that the child pages were published
        for child_page in self.pages_to_be_published:
            published_child_page = SimplePage.objects.get(id=child_page.id)
            self.assertTrue(published_child_page.live)
            self.assertIn("Hello updated", published_child_page.content)

        # Check that the descendant pages were not published
        for grandchild_pages in self.grandchildren_pages.values():
            for grandchild_page in grandchild_pages:
                self.assertFalse(Page.objects.get(id=grandchild_page.id).live)
