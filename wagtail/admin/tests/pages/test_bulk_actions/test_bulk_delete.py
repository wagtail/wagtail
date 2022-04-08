from unittest import mock

from django.contrib.auth.models import Permission
from django.db.models.signals import post_delete, pre_delete
from django.http import HttpRequest
from django.http.response import HttpResponse
from django.test import TestCase
from django.urls import reverse

from wagtail.admin.views.pages.bulk_actions.page_bulk_action import PageBulkAction
from wagtail.models import Page
from wagtail.signals import page_unpublished
from wagtail.test.testapp.models import SimplePage
from wagtail.test.utils import WagtailTestUtils


class TestBulkDelete(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add child pages
        self.child_pages = [
            SimplePage(
                title=f"Hello world!-{i}", slug=f"hello-world-{i}", content=f"hello-{i}"
            )
            for i in range(1, 5)
        ]
        # first three child pages will be deleted
        self.pages_to_be_deleted = self.child_pages[:3]
        self.pages_not_to_be_deleted = self.child_pages[3:]
        for child_page in self.child_pages:
            self.root_page.add_child(instance=child_page)

        # map of the form { page: [child_pages] } to be added
        self.grandchildren_pages = {
            self.pages_to_be_deleted[0]: [
                SimplePage(
                    title="Hello world!-a", slug="hello-world-a", content="hello-a"
                )
            ],
            self.pages_to_be_deleted[1]: [
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
                    "delete",
                ),
            )
            + "?"
        )
        for child_page in self.pages_to_be_deleted:
            self.url += f"&id={child_page.id}"

        # Login
        self.user = self.login()

    def test_bulk_delete_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # deletion should not actually happen on GET
        for child_page in self.child_pages:
            self.assertTrue(SimplePage.objects.filter(id=child_page.id).exists())

        html = response.content.decode()
        for child_page in self.pages_to_be_deleted:
            # check if the pages to be deleted and number of descendant pages are displayed
            needle = "<li>"
            needle += '<a href="{edit_page_url}" target="_blank" rel="noreferrer">{page_title}</a>'.format(
                edit_page_url=reverse("wagtailadmin_pages:edit", args=[child_page.id]),
                page_title=child_page.title,
            )
            descendants = len(self.grandchildren_pages.get(child_page, []))
            if descendants:
                needle += "<p>"
                if descendants == 1:
                    needle += "This will also delete one more subpage."
                else:
                    needle += f"This will also delete {descendants} more subpages."
                needle += "</p>"
            needle += "</li>"
            self.assertInHTML(needle, html)

    def test_page_delete_specific_admin_title(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # The number of pages to be deleted is shown on the delete confirmation page.
        self.assertContains(response, f"Delete {len(self.pages_to_be_deleted)} pages")

    def test_page_delete_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        # Get delete page
        response = self.client.get(self.url)

        # Check that the user received a 200 redirect response
        self.assertEqual(response.status_code, 200)

        # Check that the deletion has not happened
        for child_page in self.child_pages:
            self.assertTrue(SimplePage.objects.filter(id=child_page.id).exists())

        html = response.content.decode()

        self.assertInHTML(
            "<p>You don't have permission to delete these pages</p>", html
        )

        for child_page in self.pages_to_be_deleted:
            self.assertInHTML(
                "<li>{page_title}</li>".format(page_title=child_page.title), html
            )

        self.assertTagInHTML(
            """<form action="{}" method="POST"></form>""".format(self.url),
            html,
            count=0,
        )

    def test_bulk_delete_post(self):
        # Connect a mock signal handler to page_unpublished signal
        mock_handler = mock.MagicMock()
        page_unpublished.connect(mock_handler)

        # Post
        response = self.client.post(self.url)

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        # treebeard should report no consistency problems with the tree
        self.assertFalse(
            any(Page.find_problems()), "treebeard found consistency problems"
        )

        # Check that the child pages to be deleted are gone
        for child_page in self.pages_to_be_deleted:
            self.assertFalse(SimplePage.objects.filter(id=child_page.id).exists())

        # Check that the child pages not to be deleted remain
        for child_page in self.pages_not_to_be_deleted:
            self.assertTrue(SimplePage.objects.filter(id=child_page.id).exists())

        # Check that the page_unpublished signal was fired for all pages
        num_descendants = sum(len(i) for i in self.grandchildren_pages.values())
        self.assertEqual(
            mock_handler.call_count, len(self.pages_to_be_deleted) + num_descendants
        )

        i = 0
        for child_page in self.pages_to_be_deleted:
            mock_call = mock_handler.mock_calls[i][2]
            i += 1
            self.assertEqual(mock_call["sender"], child_page.specific_class)
            self.assertEqual(mock_call["instance"], child_page)
            self.assertIsInstance(mock_call["instance"], child_page.specific_class)
            for grandchildren_page in self.grandchildren_pages.get(child_page, []):
                mock_call = mock_handler.mock_calls[i][2]
                i += 1
                self.assertEqual(mock_call["sender"], grandchildren_page.specific_class)
                self.assertEqual(mock_call["instance"], grandchildren_page)
                self.assertIsInstance(
                    mock_call["instance"], grandchildren_page.specific_class
                )

    def test_bulk_delete_notlive_post(self):
        # Same as above, but this makes sure the page_unpublished signal is not fired
        # for the page that is not live when it is deleted

        # Unpublish the first child page
        page_to_be_unpublished = self.pages_to_be_deleted[0]
        page_to_be_unpublished.unpublish(user=self.user)

        # Connect a mock signal handler to page_unpublished signal
        mock_handler = mock.MagicMock()
        page_unpublished.connect(mock_handler)

        # Post
        response = self.client.post(self.url)

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        # treebeard should report no consistency problems with the tree
        self.assertFalse(
            any(Page.find_problems()), "treebeard found consistency problems"
        )

        # Check that the child pages to be deleted are gone
        for child_page in self.pages_to_be_deleted:
            self.assertFalse(SimplePage.objects.filter(id=child_page.id).exists())

        # Check that the child pages not to be deleted remain
        for child_page in self.pages_not_to_be_deleted:
            self.assertTrue(SimplePage.objects.filter(id=child_page.id).exists())

        # Check that the page_unpublished signal was not fired
        num_descendants = sum(len(v) for v in self.grandchildren_pages.values())
        self.assertEqual(
            mock_handler.call_count, len(self.pages_to_be_deleted) + num_descendants - 1
        )

        # check that only signals for other pages are fired
        i = 0
        for child_page in self.pages_to_be_deleted:
            if child_page.id != page_to_be_unpublished.id:
                mock_call = mock_handler.mock_calls[i][2]
                i += 1
                self.assertEqual(mock_call["sender"], child_page.specific_class)
                self.assertEqual(mock_call["instance"], child_page)
                self.assertIsInstance(mock_call["instance"], child_page.specific_class)
            for grandchildren_page in self.grandchildren_pages.get(child_page, []):
                mock_call = mock_handler.mock_calls[i][2]
                i += 1
                self.assertEqual(mock_call["sender"], grandchildren_page.specific_class)
                self.assertEqual(mock_call["instance"], grandchildren_page)
                self.assertIsInstance(
                    mock_call["instance"], grandchildren_page.specific_class
                )

    def test_subpage_deletion(self):
        # Connect mock signal handlers to page_unpublished, pre_delete and post_delete signals
        unpublish_signals_received = []
        pre_delete_signals_received = []
        post_delete_signals_received = []

        def page_unpublished_handler(sender, instance, **kwargs):
            unpublish_signals_received.append((sender, instance.id))

        def pre_delete_handler(sender, instance, **kwargs):
            pre_delete_signals_received.append((sender, instance.id))

        def post_delete_handler(sender, instance, **kwargs):
            post_delete_signals_received.append((sender, instance.id))

        page_unpublished.connect(page_unpublished_handler)
        pre_delete.connect(pre_delete_handler)
        post_delete.connect(post_delete_handler)

        # Post
        response = self.client.post(self.url)

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        # treebeard should report no consistency problems with the tree
        self.assertFalse(
            any(Page.find_problems()), "treebeard found consistency problems"
        )

        # Check that the child pages to be deleted are gone
        for child_page in self.pages_to_be_deleted:
            self.assertFalse(SimplePage.objects.filter(id=child_page.id).exists())

        # Check that the child pages not to be deleted remain
        for child_page in self.pages_not_to_be_deleted:
            self.assertTrue(SimplePage.objects.filter(id=child_page.id).exists())

        # Check that the subpages are also gone
        for grandchild_pages in self.grandchildren_pages.values():
            for grandchild_page in grandchild_pages:
                self.assertFalse(
                    SimplePage.objects.filter(id=grandchild_page.id).exists()
                )

        # Check that the signals were fired for all child and grandchild pages
        for child_page, grandchild_pages in self.grandchildren_pages.items():
            self.assertIn((SimplePage, child_page.id), unpublish_signals_received)
            self.assertIn((SimplePage, child_page.id), pre_delete_signals_received)
            self.assertIn((SimplePage, child_page.id), post_delete_signals_received)
            for grandchild_page in grandchild_pages:
                self.assertIn(
                    (SimplePage, grandchild_page.id), unpublish_signals_received
                )
                self.assertIn(
                    (SimplePage, grandchild_page.id), pre_delete_signals_received
                )
                self.assertIn(
                    (SimplePage, grandchild_page.id), post_delete_signals_received
                )

        self.assertEqual(response.status_code, 302)

    def test_before_delete_page_hook(self):
        def hook_func(request, action_type, pages, action_class_instance):
            self.assertEqual(action_type, "delete")
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(action_class_instance, PageBulkAction)
            for i, page in enumerate(pages):
                self.assertEqual(page.id, self.pages_to_be_deleted[i].id)
            return HttpResponse("Overridden!")

        with self.register_hook("before_bulk_action", hook_func):
            response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # Check that the child pages are not deleted
        for child_page in self.child_pages:
            self.assertTrue(SimplePage.objects.filter(id=child_page.id).exists())

    def test_after_delete_page_hook(self):
        def hook_func(request, action_type, pages, action_class_instance):
            self.assertEqual(action_type, "delete")
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(action_class_instance, PageBulkAction)
            for i, page in enumerate(pages):
                self.assertEqual(page.id, self.pages_to_be_deleted[i].id)

            return HttpResponse("Overridden!")

        with self.register_hook("after_bulk_action", hook_func):
            response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # Check that the child pages to be deleted are gone
        for child_page in self.pages_to_be_deleted:
            self.assertFalse(SimplePage.objects.filter(id=child_page.id).exists())

        # Check that the child pages not to be deleted remain
        for child_page in self.pages_not_to_be_deleted:
            self.assertTrue(SimplePage.objects.filter(id=child_page.id).exists())
