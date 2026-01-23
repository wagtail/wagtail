from unittest import mock

from django.contrib.auth.models import Permission
from django.db.models.signals import post_delete, pre_delete
from django.http import HttpRequest
from django.http.response import HttpResponse
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.http import urlencode

from wagtail.admin.views.pages.bulk_actions.page_bulk_action import PageBulkAction
from wagtail.models import Page
from wagtail.signals import page_unpublished
from wagtail.test.testapp.models import SimplePage, VariousOnDeleteModel
from wagtail.test.utils import WagtailTestUtils


class TestBulkDelete(WagtailTestUtils, TestCase):
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

        self.explore_url = reverse("wagtailadmin_explore", args=[self.root_page.id])
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
        query_params = {
            "next": self.explore_url,
            "id": [page.pk for page in self.pages_to_be_deleted],
        }
        self.url += urlencode(query_params, doseq=True)

        # Login
        self.user = self.login()

    def test_bulk_delete_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # deletion should not actually happen on GET
        for child_page in self.child_pages:
            self.assertTrue(SimplePage.objects.filter(id=child_page.id).exists())

        soup = self.get_soup(response.content)
        for child_page in self.pages_to_be_deleted:
            edit_url = reverse("wagtailadmin_pages:edit", args=[child_page.id])
            edit_link = soup.find("a", href=edit_url)
            self.assertIsNotNone(edit_link)
            self.assertEqual(
                edit_link.text.strip(),
                child_page.get_admin_display_title(),
            )
            li = edit_link.parent
            descendants = len(self.grandchildren_pages.get(child_page, []))
            if descendants:
                subpage_info = li.select_one("p")
                self.assertIsNotNone(subpage_info)
                if descendants == 1:
                    text = "This will also delete one more subpage."
                else:
                    text = f"This will also delete {descendants} more subpages."
                self.assertEqual(subpage_info.text.strip(), text)

            usage_url = (
                reverse("wagtailadmin_pages:usage", args=[child_page.id])
                + "?describe_on_delete=1"
            )
            usage_link = li.find("a", href=usage_url)
            self.assertIsNotNone(usage_link)
            self.assertEqual(
                usage_link.text.strip(),
                "This page is referenced 0 times.",
            )

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
            self.assertInHTML(f"<li>{child_page.title}</li>", html)

        self.assertTagInHTML(
            f"""<form action="{self.url}" method="POST"></form>""",
            html,
            count=0,
        )

    def test_bulk_delete_post(self):
        # Connect a mock signal handler to page_unpublished signal
        mock_handler = mock.MagicMock()
        page_unpublished.connect(mock_handler)

        try:
            # Post
            response = self.client.post(self.url)

            # Should be redirected to explorer page
            self.assertEqual(response.status_code, 302)

            # treebeard should report no consistency problems with the tree
            self.assertFalse(
                any(Page.find_problems()), msg="treebeard found consistency problems"
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
                    self.assertEqual(
                        mock_call["sender"], grandchildren_page.specific_class
                    )
                    self.assertEqual(mock_call["instance"], grandchildren_page)
                    self.assertIsInstance(
                        mock_call["instance"], grandchildren_page.specific_class
                    )
        finally:
            page_unpublished.disconnect(mock_handler)

    def test_bulk_delete_notlive_post(self):
        # Same as above, but this makes sure the page_unpublished signal is not fired
        # for the page that is not live when it is deleted

        # Unpublish the first child page
        page_to_be_unpublished = self.pages_to_be_deleted[0]
        page_to_be_unpublished.unpublish(user=self.user)

        # Connect a mock signal handler to page_unpublished signal
        mock_handler = mock.MagicMock()
        page_unpublished.connect(mock_handler)

        try:
            # Post
            response = self.client.post(self.url)

            # Should be redirected to explorer page
            self.assertEqual(response.status_code, 302)

            # treebeard should report no consistency problems with the tree
            self.assertFalse(
                any(Page.find_problems()), msg="treebeard found consistency problems"
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
                mock_handler.call_count,
                len(self.pages_to_be_deleted) + num_descendants - 1,
            )

            # check that only signals for other pages are fired
            i = 0
            for child_page in self.pages_to_be_deleted:
                if child_page.id != page_to_be_unpublished.id:
                    mock_call = mock_handler.mock_calls[i][2]
                    i += 1
                    self.assertEqual(mock_call["sender"], child_page.specific_class)
                    self.assertEqual(mock_call["instance"], child_page)
                    self.assertIsInstance(
                        mock_call["instance"], child_page.specific_class
                    )
                for grandchildren_page in self.grandchildren_pages.get(child_page, []):
                    mock_call = mock_handler.mock_calls[i][2]
                    i += 1
                    self.assertEqual(
                        mock_call["sender"], grandchildren_page.specific_class
                    )
                    self.assertEqual(mock_call["instance"], grandchildren_page)
                    self.assertIsInstance(
                        mock_call["instance"], grandchildren_page.specific_class
                    )
        finally:
            page_unpublished.disconnect(mock_handler)

    def test_subpage_deletion(self):
        # Connect mock signal handlers to page_unpublished, pre_delete and post_delete signals
        unpublish_signals_received = []
        pre_delete_signals_received = []
        post_delete_signals_received = []

        def page_unpublished_handler(sender, instance, **kwargs):
            unpublish_signals_received.append((sender, instance.pk))

        def pre_delete_handler(sender, instance, **kwargs):
            pre_delete_signals_received.append((sender, instance.pk))

        def post_delete_handler(sender, instance, **kwargs):
            post_delete_signals_received.append((sender, instance.pk))

        page_unpublished.connect(page_unpublished_handler)
        pre_delete.connect(pre_delete_handler)
        post_delete.connect(post_delete_handler)

        try:
            # Post
            response = self.client.post(self.url)

            # Should be redirected to explorer page
            self.assertEqual(response.status_code, 302)

            # treebeard should report no consistency problems with the tree
            self.assertFalse(
                any(Page.find_problems()), msg="treebeard found consistency problems"
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
        finally:
            page_unpublished.disconnect(page_unpublished_handler)
            pre_delete.disconnect(pre_delete_handler)
            post_delete.disconnect(post_delete_handler)

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

    def test_delete_get_with_protected_reference(self):
        protected = self.pages_to_be_deleted[0]
        with self.captureOnCommitCallbacks(execute=True):
            VariousOnDeleteModel.objects.create(
                text="Undeletable",
                protected_page=protected,
            )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)
        main = soup.select_one("main")
        usage_link = main.find(
            "a",
            href=reverse("wagtailadmin_pages:usage", args=[protected.pk])
            + "?describe_on_delete=1",
        )
        self.assertIsNotNone(usage_link)
        self.assertEqual(usage_link.text.strip(), "This page is referenced 1 time.")
        self.assertContains(
            response,
            "One or more references to this page prevent it from being deleted.",
        )
        submit_button = main.select_one("form button[type=submit]")
        self.assertIsNone(submit_button)
        back_button = main.find("a", href=self.explore_url)
        self.assertIsNotNone(back_button)
        self.assertEqual(back_button.text.strip(), "Go back")

    def test_delete_post_with_protected_reference(self):
        protected = self.pages_to_be_deleted[0]
        with self.captureOnCommitCallbacks(execute=True):
            VariousOnDeleteModel.objects.create(
                text="Undeletable",
                protected_page=protected,
            )
        response = self.client.post(self.url)

        # Should throw a PermissionDenied error and redirect to the dashboard
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("wagtailadmin_home"))
        self.assertEqual(
            response.context["message"],
            "Sorry, you do not have permission to access this area.",
        )

        # Check that the page is still here
        self.assertTrue(Page.objects.filter(pk=protected.pk).exists())

    @override_settings(WAGTAILADMIN_UNSAFE_PAGE_DELETION_LIMIT=10)
    def test_confirm_delete_scenario_1(self):
        """
        Bulk deletion when the number of pages is below the unsafe deletion limit.

        When fewer pages than WAGTAILADMIN_UNSAFE_PAGE_DELETION_LIMIT are
        selected for deletion:
        1. The extra typed confirmation dialog is not displayed
        2. Pages are deleted through the standard confirmation flow
        """
        url = (
            reverse(
                "wagtail_bulk_action",
                args=("wagtailcore", "page", "delete"),
            )
            + "?"
        )
        query_params = {
            "next": self.explore_url,
            "id": [page.pk for page in self.pages_to_be_deleted[:2]],
        }
        url += urlencode(query_params, doseq=True)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<input type="text" name="confirm_site_name"')
        # Check that pages have not been deleted yet (from GET request)
        for page in self.pages_to_be_deleted[:2]:
            self.assertTrue(SimplePage.objects.filter(id=page.id).exists())
        response = self.client.post(url)
        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)
        # Check that pages have been deleted (POST request)
        for page in self.pages_to_be_deleted[:2]:
            self.assertFalse(SimplePage.objects.filter(id=page.id).exists())

    @override_settings(WAGTAILADMIN_UNSAFE_PAGE_DELETION_LIMIT=1)
    @override_settings(WAGTAIL_SITE_NAME="mysite")
    def test_confirm_delete_scenario_2(self):
        """
        Bulk deletion when the number of pages is above the unsafe deletion limit.

        When more pages than WAGTAILADMIN_UNSAFE_PAGE_DELETION_LIMIT are selected for
        deletion:
        1. The extra typed confirmation dialog is displayed
        """
        url = (
            reverse(
                "wagtail_bulk_action",
                args=("wagtailcore", "page", "delete"),
            )
            + "?"
        )
        query_params = {
            "next": self.explore_url,
            "id": [page.pk for page in self.pages_to_be_deleted],
        }
        url += urlencode(query_params, doseq=True)

        # Calculate the total number of pages to delete including descendants
        total_pages = len(self.pages_to_be_deleted)
        for page in self.pages_to_be_deleted:
            total_pages += page.get_descendants().count()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, f"This action will delete <b>{total_pages}</b> pages in total."
        )
        self.assertContains(response, "Please type <b>mysite</b> to confirm.")
        self.assertContains(response, '<input type="text" name="confirm_site_name"')
        # Check that pages have not been deleted by the GET request
        for page in self.pages_to_be_deleted:
            self.assertTrue(SimplePage.objects.filter(id=page.id).exists())

        # Check that descendant pages have not been deleted by the GET request
        for parent_page, grandchild_pages in self.grandchildren_pages.items():
            for grandchild_page in grandchild_pages:
                self.assertTrue(
                    SimplePage.objects.filter(id=grandchild_page.id).exists()
                )

    @override_settings(WAGTAILADMIN_UNSAFE_PAGE_DELETION_LIMIT=3)
    @override_settings(WAGTAIL_SITE_NAME="mysite")
    def test_confirm_delete_scenario_3(self):
        """
        Bulk deletion with unsuccessful confirmation dialog.

        When a user enters an incorrect site name in the confirmation dialog:
        1. The pages are not deleted
        2. The same confirmation form is displayed again
        3. An error message is displayed
        """
        url = (
            reverse(
                "wagtail_bulk_action",
                args=("wagtailcore", "page", "delete"),
            )
            + "?"
        )
        query_params = {
            "next": self.explore_url,
            "id": [page.pk for page in self.pages_to_be_deleted],
        }
        url += urlencode(query_params, doseq=True)

        # Calculate total number of pages to delete including descendants
        total_pages = len(self.pages_to_be_deleted)
        for page in self.pages_to_be_deleted:
            total_pages += page.get_descendants().count()

        response = self.client.post(url, data={"confirm_site_name": "random"})
        self.assertEqual(response.status_code, 200)

        # Check that an error message is displayed
        messages = [m.message for m in response.context["messages"]]
        self.assertEqual(len(messages), 1)
        # Check that the confirmation form is displayed
        self.assertContains(
            response, f"This action will delete <b>{total_pages}</b> pages in total."
        )
        self.assertContains(response, "Please type <b>mysite</b> to confirm.")
        self.assertContains(response, '<input type="text" name="confirm_site_name"')

        # Check that pages have not been deleted
        for page in self.pages_to_be_deleted:
            self.assertTrue(SimplePage.objects.filter(id=page.id).exists())

        # Check that descendant pages have not been deleted
        for parent_page, grandchild_pages in self.grandchildren_pages.items():
            for grandchild_page in grandchild_pages:
                self.assertTrue(
                    SimplePage.objects.filter(id=grandchild_page.id).exists()
                )

    @override_settings(WAGTAILADMIN_UNSAFE_PAGE_DELETION_LIMIT=3)
    @override_settings(WAGTAIL_SITE_NAME="mysite")
    def test_confirm_delete_scenario_4(self):
        """
        Bulk deletion with successful confirmation dialog.

        When a user enters the correct site name in the confirmation dialog:
        1. The pages are deleted
        2. The user is redirected to the explorer page
        """
        url = (
            reverse(
                "wagtail_bulk_action",
                args=("wagtailcore", "page", "delete"),
            )
            + "?"
        )
        query_params = {
            "next": self.explore_url,
            "id": [page.pk for page in self.pages_to_be_deleted],
        }
        url += urlencode(query_params, doseq=True)

        response = self.client.post(url, data={"confirm_site_name": "mysite"})

        # Should be redirected to explorer page
        self.assertRedirects(response, self.explore_url)

        # Check that the pages are deleted
        for page in self.pages_to_be_deleted:
            self.assertFalse(SimplePage.objects.filter(id=page.id).exists())

        # Check that the descendant pages are also deleted
        for parent_page, grandchild_pages in self.grandchildren_pages.items():
            for grandchild_page in grandchild_pages:
                self.assertFalse(
                    SimplePage.objects.filter(id=grandchild_page.id).exists()
                )
