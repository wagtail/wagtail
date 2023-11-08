from django.contrib.auth.models import Group, Permission
from django.http import HttpRequest, HttpResponse
from django.test import TestCase
from django.urls import reverse

from wagtail.models import GroupPagePermission, Page
from wagtail.test.testapp.models import (
    EventPage,
    EventPageSpeaker,
    PageWithExcludedCopyField,
    SimplePage,
)
from wagtail.test.utils import WagtailTestUtils


class TestPageCopy(WagtailTestUtils, TestCase):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Create a page
        self.test_page = self.root_page.add_child(
            instance=SimplePage(
                title="Hello world!",
                slug="hello-world",
                content="hello",
                live=True,
                has_unpublished_changes=False,
            )
        )

        # Create a couple of child pages
        self.test_child_page = self.test_page.add_child(
            instance=SimplePage(
                title="Child page",
                slug="child-page",
                content="hello",
                live=True,
                has_unpublished_changes=True,
            )
        )

        self.test_unpublished_child_page = self.test_page.add_child(
            instance=SimplePage(
                title="Unpublished Child page",
                slug="unpublished-child-page",
                content="hello",
                live=False,
                has_unpublished_changes=True,
            )
        )

        # Login
        self.user = self.login()

    def test_page_copy(self):
        response = self.client.get(
            reverse("wagtailadmin_pages:copy", args=(self.test_page.id,))
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/copy.html")

        # Make sure all fields are in the form
        self.assertContains(response, "New title")
        self.assertContains(response, "New slug")
        self.assertContains(response, "New parent page")
        self.assertContains(response, "Copy subpages")
        self.assertContains(response, "Publish copies")
        self.assertContains(response, "Alias")

    def test_page_copy_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        # Get copy page
        post_data = {
            "new_title": "Hello world 2",
            "new_slug": "hello-world",
            "new_parent_page": str(self.test_page.id),
            "copy_subpages": False,
            "alias": False,
        }
        response = self.client.post(
            reverse("wagtailadmin_pages:copy", args=(self.test_page.id,)), post_data
        )

        # A user with no page permissions at all should be redirected to the admin home
        self.assertRedirects(response, reverse("wagtailadmin_home"))

        # A user with page permissions, but not add permission at the destination,
        # should receive a form validation error
        publishers = Group.objects.create(name="Publishers")
        GroupPagePermission.objects.create(
            group=publishers, page=self.root_page, permission_type="publish"
        )
        self.user.groups.add(publishers)
        self.user.save()

        # Get copy page
        post_data = {
            "new_title": "Hello world 2",
            "new_slug": "hello-world",
            "new_parent_page": str(self.test_page.id),
            "copy_subpages": False,
            "alias": False,
        }
        response = self.client.post(
            reverse("wagtailadmin_pages:copy", args=(self.test_page.id,)), post_data
        )
        form = response.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("new_parent_page", form.errors)

    def test_page_copy_post(self):
        post_data = {
            "new_title": "Hello world 2",
            "new_slug": "hello-world-2",
            "new_parent_page": str(self.root_page.id),
            "copy_subpages": False,
            "publish_copies": False,
            "alias": False,
        }
        response = self.client.post(
            reverse("wagtailadmin_pages:copy", args=(self.test_page.id,)), post_data
        )

        # Check that the user was redirected to the parents explore page
        self.assertRedirects(
            response, reverse("wagtailadmin_explore", args=(self.root_page.id,))
        )

        # Get copy
        page_copy = self.root_page.get_children().filter(slug="hello-world-2").first()

        # Check that the copy exists
        self.assertIsNotNone(page_copy)

        # Check that the copy is not live
        self.assertFalse(page_copy.live)
        self.assertTrue(page_copy.has_unpublished_changes)

        # Check that the owner of the page is set correctly
        self.assertEqual(page_copy.owner, self.user)

        # Check that the children were not copied
        self.assertEqual(page_copy.get_children().count(), 0)

        # treebeard should report no consistency problems with the tree
        self.assertFalse(
            any(Page.find_problems()), msg="treebeard found consistency problems"
        )

    def test_page_with_exclude_fields_in_copy(self):
        original_page = self.test_page.add_child(
            instance=PageWithExcludedCopyField(
                title="Page with exclude_fields_in_copy",
                slug="page-with-exclude-fields-in-copy",
                content="Copy me",
                special_field="Don't copy me",
                live=True,
                has_unpublished_changes=False,
            )
        )
        post_data = {
            "new_title": f"{original_page.title} 2",
            "new_slug": f"{original_page.slug}-2",
            "new_parent_page": str(self.root_page.id),
            "copy_subpages": False,
            "publish_copies": False,
            "alias": False,
        }
        self.client.post(
            reverse("wagtailadmin_pages:copy", args=(original_page.id,)), post_data
        )
        # Get copy
        page_copy = PageWithExcludedCopyField.objects.get(slug=post_data["new_slug"])
        self.assertEqual(page_copy.content, original_page.content)
        self.assertNotEqual(page_copy.special_field, original_page.special_field)
        self.assertEqual(
            page_copy.special_field, page_copy._meta.get_field("special_field").default
        )

    def test_page_copy_post_copy_subpages(self):
        post_data = {
            "new_title": "Hello world 2",
            "new_slug": "hello-world-2",
            "new_parent_page": str(self.root_page.id),
            "copy_subpages": True,
            "publish_copies": False,
            "alias": False,
        }
        response = self.client.post(
            reverse("wagtailadmin_pages:copy", args=(self.test_page.id,)), post_data
        )

        # Check that the user was redirected to the parents explore page
        self.assertRedirects(
            response, reverse("wagtailadmin_explore", args=(self.root_page.id,))
        )

        # Get copy
        page_copy = self.root_page.get_children().filter(slug="hello-world-2").first()

        # Check that the copy exists
        self.assertIsNotNone(page_copy)

        # Check that the copy is not live
        self.assertFalse(page_copy.live)
        self.assertTrue(page_copy.has_unpublished_changes)

        # Check that the owner of the page is set correctly
        self.assertEqual(page_copy.owner, self.user)

        # Check that the children were copied
        self.assertEqual(page_copy.get_children().count(), 2)

        # Check the child pages
        # Neither of them should be live
        child_copy = page_copy.get_children().filter(slug="child-page").first()
        self.assertIsNotNone(child_copy)
        self.assertFalse(child_copy.live)
        self.assertTrue(child_copy.has_unpublished_changes)

        unpublished_child_copy = (
            page_copy.get_children().filter(slug="unpublished-child-page").first()
        )
        self.assertIsNotNone(unpublished_child_copy)
        self.assertFalse(unpublished_child_copy.live)
        self.assertTrue(unpublished_child_copy.has_unpublished_changes)

        # treebeard should report no consistency problems with the tree
        self.assertFalse(
            any(Page.find_problems()), msg="treebeard found consistency problems"
        )

    def test_page_copy_post_copy_subpages_publish_copies(self):
        post_data = {
            "new_title": "Hello world 2",
            "new_slug": "hello-world-2",
            "new_parent_page": str(self.root_page.id),
            "copy_subpages": True,
            "publish_copies": True,
            "alias": False,
        }
        response = self.client.post(
            reverse("wagtailadmin_pages:copy", args=(self.test_page.id,)), post_data
        )

        # Check that the user was redirected to the parents explore page
        self.assertRedirects(
            response, reverse("wagtailadmin_explore", args=(self.root_page.id,))
        )

        # Get copy
        page_copy = self.root_page.get_children().filter(slug="hello-world-2").first()

        # Check that the copy exists
        self.assertIsNotNone(page_copy)

        # Check that the copy is live
        self.assertTrue(page_copy.live)
        self.assertFalse(page_copy.has_unpublished_changes)

        # Check that the owner of the page is set correctly
        self.assertEqual(page_copy.owner, self.user)

        # Check that the children were copied
        self.assertEqual(page_copy.get_children().count(), 2)

        # Check the child pages
        # The child_copy should be live but the unpublished_child_copy shouldn't
        child_copy = page_copy.get_children().filter(slug="child-page").first()
        self.assertIsNotNone(child_copy)
        self.assertTrue(child_copy.live)
        self.assertTrue(child_copy.has_unpublished_changes)

        unpublished_child_copy = (
            page_copy.get_children().filter(slug="unpublished-child-page").first()
        )
        self.assertIsNotNone(unpublished_child_copy)
        self.assertFalse(unpublished_child_copy.live)
        self.assertTrue(unpublished_child_copy.has_unpublished_changes)

        # treebeard should report no consistency problems with the tree
        self.assertFalse(
            any(Page.find_problems()), msg="treebeard found consistency problems"
        )

    def test_page_copy_post_new_parent(self):
        post_data = {
            "new_title": "Hello world 2",
            "new_slug": "hello-world-2",
            "new_parent_page": str(self.test_child_page.id),
            "copy_subpages": False,
            "publish_copies": False,
            "alias": False,
        }
        response = self.client.post(
            reverse("wagtailadmin_pages:copy", args=(self.test_page.id,)), post_data
        )

        # Check that the user was redirected to the new parents explore page
        self.assertRedirects(
            response, reverse("wagtailadmin_explore", args=(self.test_child_page.id,))
        )

        # Check that the page was copied to the correct place
        self.assertTrue(
            Page.objects.filter(slug="hello-world-2").first().get_parent(),
            msg=self.test_child_page,
        )

        # treebeard should report no consistency problems with the tree
        self.assertFalse(
            any(Page.find_problems()), msg="treebeard found consistency problems"
        )

    def test_page_copy_post_existing_slug_within_same_parent_page(self):
        # This tests the existing slug checking on page copy when not changing the parent page

        # Attempt to copy the page but forget to change the slug
        post_data = {
            "new_title": "Hello world 2",
            "new_slug": "hello-world",
            "new_parent_page": str(self.root_page.id),
            "copy_subpages": False,
            "alias": False,
        }
        response = self.client.post(
            reverse("wagtailadmin_pages:copy", args=(self.test_page.id,)), post_data
        )

        # Should not be redirected (as the save should fail)
        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(
            response,
            "form",
            "new_slug",
            'This slug is already in use within the context of its parent page "Welcome to your new Wagtail site!"',
        )

    def test_page_copy_post_and_subpages_to_same_tree_branch(self):
        # This tests that a page cannot be copied into itself when copying subpages
        post_data = {
            "new_title": "Hello world 2",
            "new_slug": "hello-world",
            "new_parent_page": str(self.test_child_page.id),
            "copy_subpages": True,
            "alias": False,
        }
        response = self.client.post(
            reverse("wagtailadmin_pages:copy", args=(self.test_page.id,)), post_data
        )

        # Should not be redirected (as the save should fail)
        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(
            response,
            "form",
            "new_parent_page",
            "You cannot copy a page into itself when copying subpages",
        )

    def test_page_copy_post_existing_slug_to_another_parent_page(self):
        # This tests the existing slug checking on page copy when changing the parent page

        # Attempt to copy the page and changed the parent page
        post_data = {
            "new_title": "Hello world 2",
            "new_slug": "hello-world",
            "new_parent_page": str(self.test_child_page.id),
            "copy_subpages": False,
            "alias": False,
        }
        response = self.client.post(
            reverse("wagtailadmin_pages:copy", args=(self.test_page.id,)), post_data
        )

        # Check that the user was redirected to the parents explore page
        self.assertRedirects(
            response, reverse("wagtailadmin_explore", args=(self.test_child_page.id,))
        )

    def test_page_copy_post_invalid_slug(self):
        # Attempt to copy the page but set an invalid slug string
        post_data = {
            "new_title": "Hello world 2",
            "new_slug": "hello world!",
            "new_parent_page": str(self.root_page.id),
            "copy_subpages": False,
            "alias": False,
        }
        response = self.client.post(
            reverse("wagtailadmin_pages:copy", args=(self.test_page.id,)), post_data
        )

        # Should not be redirected (as the save should fail)
        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(
            response,
            "form",
            "new_slug",
            "Enter a valid “slug” consisting of Unicode letters, numbers, underscores, or hyphens.",
        )

    def test_page_copy_post_valid_unicode_slug(self):
        post_data = {
            "new_title": "Hello wɜːld",
            "new_slug": "hello-wɜːld",
            "new_parent_page": str(self.test_page.id),
            "copy_subpages": False,
            "alias": False,
        }
        response = self.client.post(
            reverse("wagtailadmin_pages:copy", args=(self.test_page.id,)), post_data
        )

        # Check response
        self.assertRedirects(
            response, reverse("wagtailadmin_explore", args=(self.test_page.id,))
        )

        # Get copy
        page_copy = (
            self.test_page.get_children().filter(slug=post_data["new_slug"]).first()
        )

        # Check that the copy exists with the good slug
        self.assertIsNotNone(page_copy)
        self.assertEqual(page_copy.slug, post_data["new_slug"])

    def test_page_copy_no_publish_permission(self):
        # Turn user into an editor who can add pages but not publish them
        self.user.is_superuser = False
        self.user.groups.add(
            Group.objects.get(name="Editors"),
        )
        self.user.save()

        # Get copy page
        response = self.client.get(
            reverse("wagtailadmin_pages:copy", args=(self.test_page.id,))
        )

        # The user should have access to the copy page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/copy.html")

        # Make sure the "publish copies" field is hidden
        self.assertNotContains(response, "Publish copies")

    def test_page_copy_no_publish_permission_post_copy_subpages_publish_copies(self):
        # This tests that unprivileged users cannot publish copied pages even if they hack their browser

        # Turn user into an editor who can add pages but not publish them
        self.user.is_superuser = False
        self.user.groups.add(
            Group.objects.get(name="Editors"),
        )
        self.user.save()

        # Post
        post_data = {
            "new_title": "Hello world 2",
            "new_slug": "hello-world-2",
            "new_parent_page": str(self.root_page.id),
            "copy_subpages": True,
            "publish_copies": True,
            "alias": False,
        }
        response = self.client.post(
            reverse("wagtailadmin_pages:copy", args=(self.test_page.id,)), post_data
        )

        # Check that the user was redirected to the parents explore page
        self.assertRedirects(
            response, reverse("wagtailadmin_explore", args=(self.root_page.id,))
        )

        # Get copy
        page_copy = self.root_page.get_children().filter(slug="hello-world-2").first()

        # Check that the copy exists
        self.assertIsNotNone(page_copy)

        # Check that the copy is not live
        self.assertFalse(page_copy.live)

        # Check that the owner of the page is set correctly
        self.assertEqual(page_copy.owner, self.user)

        # Check that the children were copied
        self.assertEqual(page_copy.get_children().count(), 2)

        # Check the child pages
        # Neither of them should be live
        child_copy = page_copy.get_children().filter(slug="child-page").first()
        self.assertIsNotNone(child_copy)
        self.assertFalse(child_copy.live)

        unpublished_child_copy = (
            page_copy.get_children().filter(slug="unpublished-child-page").first()
        )
        self.assertIsNotNone(unpublished_child_copy)
        self.assertFalse(unpublished_child_copy.live)

        # treebeard should report no consistency problems with the tree
        self.assertFalse(
            any(Page.find_problems()), msg="treebeard found consistency problems"
        )

    def test_before_copy_page_hook(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(page.specific, SimplePage)

            return HttpResponse("Overridden!")

        with self.register_hook("before_copy_page", hook_func):
            response = self.client.get(
                reverse("wagtailadmin_pages:copy", args=(self.test_page.id,))
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

    def test_before_copy_page_hook_post(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(page.specific, SimplePage)

            return HttpResponse("Overridden!")

        with self.register_hook("before_copy_page", hook_func):
            post_data = {
                "new_title": "Hello world 2",
                "new_slug": "hello-world-2",
                "new_parent_page": str(self.root_page.id),
                "copy_subpages": False,
                "publish_copies": False,
                "alias": False,
            }
            response = self.client.post(
                reverse("wagtailadmin_pages:copy", args=(self.test_page.id,)), post_data
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # page should not be copied
        self.assertFalse(Page.objects.filter(title="Hello world 2").exists())

    def test_after_copy_page_hook(self):
        def hook_func(request, page, new_page):
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(page.specific, SimplePage)
            self.assertIsInstance(new_page.specific, SimplePage)

            return HttpResponse("Overridden!")

        with self.register_hook("after_copy_page", hook_func):
            post_data = {
                "new_title": "Hello world 2",
                "new_slug": "hello-world-2",
                "new_parent_page": str(self.root_page.id),
                "copy_subpages": False,
                "publish_copies": False,
                "alias": False,
            }
            response = self.client.post(
                reverse("wagtailadmin_pages:copy", args=(self.test_page.id,)), post_data
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # page should be copied
        self.assertTrue(Page.objects.filter(title="Hello world 2").exists())

    def test_page_copy_alias_post(self):
        post_data = {
            "new_title": "Hello world 2",
            "new_slug": "hello-world-2",
            "new_parent_page": str(self.root_page.id),
            "copy_subpages": False,
            "publish_copies": False,
            "alias": True,
        }
        response = self.client.post(
            reverse("wagtailadmin_pages:copy", args=(self.test_page.id,)), post_data
        )

        # Check that the user was redirected to the parents explore page
        self.assertRedirects(
            response, reverse("wagtailadmin_explore", args=(self.root_page.id,))
        )

        # Get copy
        page_copy = self.root_page.get_children().get(slug="hello-world-2")

        # Check the copy is an alias of the original
        self.assertEqual(page_copy.alias_of, self.test_page.page_ptr)

        # Check that the copy is live
        # Note: publish_copies is ignored. Alias pages always keep the same state as their original
        self.assertTrue(page_copy.live)
        self.assertFalse(page_copy.has_unpublished_changes)

        # Check that the owner of the page is set correctly
        self.assertEqual(page_copy.owner, self.user)

        # Check that the children were not copied
        self.assertEqual(page_copy.get_children().count(), 0)

        # treebeard should report no consistency problems with the tree
        self.assertFalse(
            any(Page.find_problems()), msg="treebeard found consistency problems"
        )

    def test_page_copy_alias_post_copy_subpages(self):
        post_data = {
            "new_title": "Hello world 2",
            "new_slug": "hello-world-2",
            "new_parent_page": str(self.root_page.id),
            "copy_subpages": True,
            "publish_copies": False,
            "alias": True,
        }
        response = self.client.post(
            reverse("wagtailadmin_pages:copy", args=(self.test_page.id,)), post_data
        )

        # Check that the user was redirected to the parents explore page
        self.assertRedirects(
            response, reverse("wagtailadmin_explore", args=(self.root_page.id,))
        )

        # Get copy
        page_copy = self.root_page.get_children().get(slug="hello-world-2")

        # Check the copy is an alias of the original
        self.assertEqual(page_copy.alias_of, self.test_page.page_ptr)

        # Check that the copy is live
        # Note: publish_copies is ignored. Alias pages always keep the same state as their original
        self.assertTrue(page_copy.live)
        self.assertFalse(page_copy.has_unpublished_changes)

        # Check that the owner of the page is set correctly
        self.assertEqual(page_copy.owner, self.user)

        # Check that the children were copied
        self.assertEqual(page_copy.get_children().count(), 2)

        # Check the child pages
        # Neither of them should be live
        child_copy = page_copy.get_children().filter(slug="child-page").first()
        self.assertIsNotNone(child_copy)
        self.assertEqual(child_copy.alias_of, self.test_child_page.page_ptr)
        self.assertTrue(child_copy.live)
        self.assertFalse(child_copy.has_unpublished_changes)

        unpublished_child_copy = (
            page_copy.get_children().filter(slug="unpublished-child-page").first()
        )
        self.assertIsNotNone(unpublished_child_copy)
        self.assertEqual(
            unpublished_child_copy.alias_of, self.test_unpublished_child_page.page_ptr
        )
        self.assertFalse(unpublished_child_copy.live)
        self.assertTrue(unpublished_child_copy.has_unpublished_changes)

        # treebeard should report no consistency problems with the tree
        self.assertFalse(
            any(Page.find_problems()), msg="treebeard found consistency problems"
        )

    def test_page_copy_alias_post_without_source_publish_permission(self):
        # Check for issue #7293 - If the user has permission to publish at a destination, but not the source.
        # Wagtail would crash on attempt to copy

        # Create a new section
        self.destination_page = self.root_page.add_child(
            instance=SimplePage(
                title="Destination page",
                slug="destination-page",
                content="hello",
                live=True,
                has_unpublished_changes=False,
            )
        )

        # Make user a moderator and make it so they can only publish at the destination page
        self.user.is_superuser = False
        self.user.groups.add(Group.objects.get(name="Moderators"))
        self.user.save()
        GroupPagePermission.objects.filter(permission__codename="publish_page").update(
            page=self.destination_page
        )

        post_data = {
            "new_title": self.test_child_page.title,
            "new_slug": self.test_child_page.slug,
            "new_parent_page": str(self.destination_page.id),
            "copy_subpages": False,
            "publish_copies": False,
            "alias": False,
        }
        response = self.client.post(
            reverse("wagtailadmin_pages:copy", args=[self.test_child_page.id]),
            post_data,
        )

        # We only need to check that it didn't crash
        self.assertEqual(response.status_code, 302)

    def test_copy_page_with_unique_uuids_in_orderables(self):
        """
        Test that a page with orderables can be copied and the translation
        keys are updated.
        """
        event_page = EventPage(
            title="Moon Landing",
            location="the moon",
            audience="public",
            cost="free on TV",
            date_from="1969-07-20",
        )
        self.root_page.add_child(instance=event_page)

        event_page.speakers.add(
            EventPageSpeaker(
                first_name="Neil",
                last_name="Armstrong",
            )
        )
        # ensure there's a revision (which should capture the new speaker orderables)
        # before copying the page
        event_page.save_revision().publish()

        post_data = {
            "new_title": "New Moon landing",
            "new_slug": "moon-landing-redux",
            "new_parent_page": str(self.root_page.id),
            "copy_subpages": False,
            "publish_copies": False,
            "alias": False,
        }
        self.client.post(
            reverse("wagtailadmin_pages:copy", args=[event_page.id]), post_data
        )
        new_page = EventPage.objects.last()

        # Hack: get the page instance from the edit form which assembles it from the
        # latest revision. While we could do new_page.get_latest_revision().as_object()
        # this follow the edit view closer and should it change the test is less
        # prone to continue working because we're skipping some step
        response = self.client.get(
            reverse("wagtailadmin_pages:edit", args=[new_page.id])
        )
        new_page_on_edit_form = response.context["form"].instance

        # publish the page, similar to EditView.publish_action()
        new_page_on_edit_form.save_revision().publish()

        self.assertNotEqual(
            event_page.speakers.first().translation_key,
            new_page.speakers.first().translation_key,
        )
