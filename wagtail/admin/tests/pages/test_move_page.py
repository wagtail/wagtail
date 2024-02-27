from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.messages import constants as message_constants
from django.http import HttpRequest, HttpResponse
from django.test import TestCase
from django.urls import reverse

from wagtail.models import Page
from wagtail.signals import post_page_move, pre_page_move
from wagtail.test.testapp.models import BusinessSubIndex, SimplePage
from wagtail.test.utils import WagtailTestUtils


class TestPageMove(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    @classmethod
    def setUpTestData(cls):
        # Find root page
        cls.root_page = Page.objects.get(id=2)

        # Create three sections
        cls.section_a = SimplePage(title="Section A", slug="section-a", content="hello")
        cls.root_page.add_child(instance=cls.section_a)

        cls.section_b = SimplePage(title="Section B", slug="section-b", content="hello")
        cls.root_page.add_child(instance=cls.section_b)

        cls.section_c = SimplePage(title="Section C", slug="section-c", content="hello")
        cls.root_page.add_child(instance=cls.section_c)

        # Add test page A into section A
        cls.test_page_a = SimplePage(
            title="Hello world!", slug="hello-world", content="hello"
        )
        cls.section_a.add_child(instance=cls.test_page_a)

        # Add test page B into section C
        cls.test_page_b = SimplePage(
            title="Hello world!", slug="hello-world", content="hello"
        )
        cls.section_c.add_child(instance=cls.test_page_b)

        # Add unpublished page to the root with a child page
        cls.unpublished_page = SimplePage(
            title="Unpublished", slug="unpublished", content="hello"
        )
        sub_page = SimplePage(title="Sub Page", slug="sub-page", content="child")
        cls.root_page.add_child(instance=cls.unpublished_page)
        cls.unpublished_page.add_child(instance=sub_page)

        # unpublish pages last (used to validate the edit only permission)
        cls.unpublished_page.unpublish()
        sub_page.unpublish()

    def setUp(self):
        # Login
        self.user = self.login()

    def test_page_move(self):
        response = self.client.get(
            reverse("wagtailadmin_pages:move", args=(self.test_page_a.id,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.section_a.title)

    def test_page_move_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        # Get move page
        response = self.client.get(
            reverse("wagtailadmin_pages:move", args=(self.test_page_a.id,))
        )

        # Check that the user received a 302 redirected response
        self.assertEqual(response.status_code, 302)

    def test_user_without_bulk_delete_permission_can_move(self):
        # to verify that a user without bulk delete permission is able to move a page with a child page

        self.client.logout()
        user = get_user_model().objects.get(email="siteeditor@example.com")
        self.login(user)

        # ensure the bulk_delete is not applicable to this user
        can_bulk_delete = self.test_page_b.permissions_for_user(user).can_delete()
        self.assertFalse(can_bulk_delete)

        response = self.client.get(
            reverse("wagtailadmin_pages:move", args=(self.unpublished_page.id,))
        )

        self.assertEqual(response.status_code, 200)

    def test_page_move_confirm(self):
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:move_confirm",
                args=(self.test_page_a.id, self.section_b.id),
            )
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            reverse(
                "wagtailadmin_pages:move_confirm",
                args=(self.test_page_b.id, self.section_a.id),
            )
        )
        # Duplicate slugs triggers a redirect with an error message.
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse("wagtailadmin_home"))
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level, message_constants.ERROR)
        # Slug should be in error message.
        self.assertIn(self.test_page_b.slug, messages[0].message)

    def test_move_triggers_signals(self):
        # Connect a mock signal handler to pre_page_move and post_page_move signals
        pre_moved_handler = mock.MagicMock()
        post_moved_handler = mock.MagicMock()

        pre_page_move.connect(pre_moved_handler)
        post_page_move.connect(post_moved_handler)

        # Post to view to move page
        try:
            self.client.post(
                reverse(
                    "wagtailadmin_pages:move_confirm",
                    args=(self.test_page_a.id, self.section_b.id),
                )
            )
        finally:
            # Disconnect mock handler to prevent cross-test pollution
            pre_page_move.disconnect(pre_moved_handler)
            post_page_move.disconnect(post_moved_handler)

        # parent_page_before returns the non-specific page type, and that's OK
        nonspecific_section_a = Page.objects.get(pk=self.section_a.pk)

        # Check that the pre_page_move signal was fired
        self.assertEqual(pre_moved_handler.call_count, 1)
        pre_moved_handler.assert_called_with(
            signal=mock.ANY,
            sender=self.test_page_a.specific_class,
            instance=self.test_page_a,
            parent_page_before=nonspecific_section_a,
            parent_page_after=self.section_b,
            url_path_before="/home/section-a/hello-world/",
            url_path_after="/home/section-b/hello-world/",
        )

        # Check that the post_page_move signal was fired
        self.assertEqual(post_moved_handler.call_count, 1)
        post_moved_handler.assert_called_with(
            signal=mock.ANY,
            sender=self.test_page_a.specific_class,
            # during the move operation, we reloaded the page as a non-specific instance
            instance=Page.objects.get(pk=self.test_page_a.pk),
            parent_page_before=nonspecific_section_a,
            parent_page_after=self.section_b,
            url_path_before="/home/section-a/hello-world/",
            url_path_after="/home/section-b/hello-world/",
        )

    def test_before_move_page_hook(self):
        def hook_func(request, page, destination):
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(page.specific, SimplePage)
            self.assertIsInstance(destination.specific, SimplePage)

            return HttpResponse("Overridden!")

        with self.register_hook("before_move_page", hook_func):
            response = self.client.get(
                reverse(
                    "wagtailadmin_pages:move_confirm",
                    args=(self.test_page_a.id, self.section_b.id),
                )
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

    def test_before_move_page_hook_post(self):
        def hook_func(request, page, destination):
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(page.specific, SimplePage)
            self.assertIsInstance(destination.specific, SimplePage)

            return HttpResponse("Overridden!")

        with self.register_hook("before_move_page", hook_func):
            response = self.client.post(
                reverse(
                    "wagtailadmin_pages:move_confirm",
                    args=(self.test_page_a.id, self.section_b.id),
                )
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # page should not be moved
        self.assertEqual(
            Page.objects.get(id=self.test_page_a.id).get_parent().id, self.section_a.id
        )

    def test_after_move_page_hook(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(page.specific, SimplePage)

            return HttpResponse("Overridden!")

        with self.register_hook("after_move_page", hook_func):
            response = self.client.post(
                reverse(
                    "wagtailadmin_pages:move_confirm",
                    args=(self.test_page_a.id, self.section_b.id),
                )
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # page should be moved
        self.assertEqual(
            Page.objects.get(id=self.test_page_a.id).get_parent().id, self.section_b.id
        )

    def test_page_move_after_parent_page_types_changes_to_different_parent_model(self):
        # Test for issue #10348
        # While BusinessSubIndex cannot be created under a SimplePage, we can
        # still create it under a SimplePage invoking django-treebeard's add_child
        # which works great for our purposes.
        self.assertFalse(BusinessSubIndex.can_exist_under(self.section_a))
        page = self.section_a.add_child(
            instance=BusinessSubIndex(
                title="Business Sub Index",
                slug="business-sub-index",
                live=True,
                has_unpublished_changes=False,
            )
        )

        response = self.client.get(reverse("wagtailadmin_pages:move", args=(page.id,)))
        self.assertEqual(response.status_code, 200)

        form = response.context["move_form"]
        self.assertEqual(form.fields["new_parent_page"].initial.pk, self.section_a.pk)
        self.assertNotContains(response, self.section_a.title)
