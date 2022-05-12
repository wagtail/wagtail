import datetime
import unittest
from unittest import mock

from django.contrib.auth.models import Group, Permission
from django.http import HttpRequest, HttpResponse
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from wagtail.admin.tests.pages.timestamps import submittable_timestamp
from wagtail.models import GroupPagePermission, Locale, Page, PageRevision
from wagtail.signals import page_published
from wagtail.test.testapp.models import (
    BusinessChild,
    BusinessIndex,
    BusinessSubIndex,
    DefaultStreamPage,
    PersonPage,
    SimplePage,
    SingletonPage,
    SingletonPageViaMaxCount,
    StandardChild,
    StandardIndex,
)
from wagtail.test.utils import WagtailTestUtils


class TestPageCreation(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Login
        self.user = self.login()

    def test_add_subpage(self):
        response = self.client.get(
            reverse("wagtailadmin_pages:add_subpage", args=(self.root_page.id,))
        )
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Simple page")
        target_url = reverse(
            "wagtailadmin_pages:add", args=("tests", "simplepage", self.root_page.id)
        )
        self.assertContains(response, 'href="%s"' % target_url)
        self.assertContains(response, "A simple page description")
        # List of available page types should not contain pages with is_creatable = False
        self.assertNotContains(response, "MTI base page")
        # List of available page types should not contain abstract pages
        self.assertNotContains(response, "Abstract page")
        # List of available page types should not contain pages whose parent_page_types forbid it
        self.assertNotContains(response, "Business child")

    def test_add_subpage_with_subpage_types(self):
        # Add a BusinessIndex to test business rules in
        business_index = BusinessIndex(
            title="Hello world!",
            slug="hello-world",
        )
        self.root_page.add_child(instance=business_index)

        response = self.client.get(
            reverse("wagtailadmin_pages:add_subpage", args=(business_index.id,))
        )
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Business child")
        self.assertContains(response, "A lazy business child page description")
        # List should not contain page types not in the subpage_types list
        self.assertNotContains(response, "Simple page")

    def test_add_subpage_with_one_valid_subpage_type(self):
        # Add a BusinessSubIndex to test business rules in
        business_index = BusinessIndex(
            title="Hello world!",
            slug="hello-world",
        )
        self.root_page.add_child(instance=business_index)
        business_subindex = BusinessSubIndex(
            title="Hello world!",
            slug="hello-world",
        )
        business_index.add_child(instance=business_subindex)

        response = self.client.get(
            reverse("wagtailadmin_pages:add_subpage", args=(business_subindex.id,))
        )
        # Should be redirected to the 'add' page for BusinessChild, the only valid subpage type
        self.assertRedirects(
            response,
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "businesschild", business_subindex.id),
            ),
        )

    def test_add_subpage_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        # Get add subpage page
        response = self.client.get(
            reverse("wagtailadmin_pages:add_subpage", args=(self.root_page.id,))
        )

        # Check that the user received a 403 response
        self.assertEqual(response.status_code, 302)

    def test_add_subpage_nonexistantparent(self):
        response = self.client.get(
            reverse("wagtailadmin_pages:add_subpage", args=(100000,))
        )
        self.assertEqual(response.status_code, 404)

    def test_add_subpage_with_next_param(self):
        response = self.client.get(
            reverse("wagtailadmin_pages:add_subpage", args=(self.root_page.id,)),
            {"next": "/admin/users/"},
        )
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Simple page")
        target_url = reverse(
            "wagtailadmin_pages:add", args=("tests", "simplepage", self.root_page.id)
        )
        self.assertContains(response, 'href="%s?next=/admin/users/"' % target_url)

    def test_create_simplepage(self):
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "simplepage", self.root_page.id),
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/html; charset=utf-8")
        self.assertContains(
            response,
            '<a id="tab-label-content" href="#tab-content" class="w-tabs__tab " role="tab" aria-selected="false" tabindex="-1">',
        )
        self.assertContains(
            response,
            '<a id="tab-label-promote" href="#tab-promote" class="w-tabs__tab " role="tab" aria-selected="false" tabindex="-1">',
        )
        # test register_page_action_menu_item hook
        self.assertContains(
            response,
            '<button type="submit" name="action-panic" value="Panic!" class="button">Panic!</button>',
        )
        self.assertContains(response, "testapp/js/siren.js")
        # test construct_page_action_menu hook
        self.assertContains(
            response,
            '<button type="submit" name="action-relax" value="Relax." class="button">Relax.</button>',
        )
        # test that workflow actions are shown
        self.assertContains(
            response,
            '<button type="submit" name="action-submit" value="Submit for moderation" class="button">',
        )

    @override_settings(WAGTAIL_WORKFLOW_ENABLED=False)
    def test_workflow_buttons_not_shown_when_workflow_disabled(self):
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "simplepage", self.root_page.id),
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'value="Submit for moderation"')

    def test_create_multipart(self):
        """
        Test checks if 'enctype="multipart/form-data"' is added and only to forms that require multipart encoding.
        """
        # check for SimplePage where is no file field
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "simplepage", self.root_page.id),
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'enctype="multipart/form-data"')
        self.assertTemplateUsed(response, "wagtailadmin/pages/create.html")

        # check for FilePage which has file field
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add", args=("tests", "filepage", self.root_page.id)
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'enctype="multipart/form-data"')

    def test_create_page_without_promote_tab(self):
        """
        Test that the Promote tab is not rendered for page classes that define it as empty
        """
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "standardindex", self.root_page.id),
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<a id="tab-label-content" href="#tab-content" class="w-tabs__tab " role="tab" aria-selected="false" tabindex="-1">',
        )
        self.assertNotContains(response, "tab-promote")

    def test_create_page_with_custom_tabs(self):
        """
        Test that custom edit handlers are rendered
        """
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "standardchild", self.root_page.id),
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<a id="tab-label-content" href="#tab-content" class="w-tabs__tab " role="tab" aria-selected="false" tabindex="-1">',
        )
        self.assertContains(
            response,
            '<a id="tab-label-promote" href="#tab-promote" class="w-tabs__tab " role="tab" aria-selected="false" tabindex="-1">',
        )
        self.assertContains(
            response,
            '<a id="tab-label-dinosaurs" href="#tab-dinosaurs" class="w-tabs__tab " role="tab" aria-selected="false" tabindex="-1">',
        )

    def test_create_page_with_non_model_field(self):
        """
        Test that additional fields defined on the form rather than the model are accepted and rendered
        """
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "formclassadditionalfieldpage", self.root_page.id),
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/create.html")
        self.assertContains(response, "Enter SMS authentication code")

    def test_create_simplepage_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        # Get page
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=(
                    "tests",
                    "simplepage",
                    self.root_page.id,
                ),
            )
        )

        # Check that the user received a 403 response
        self.assertEqual(response.status_code, 302)

    def test_cannot_create_page_with_is_creatable_false(self):
        # tests.MTIBasePage has is_creatable=False, so attempting to add a new one
        # should fail with permission denied
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "mtibasepage", self.root_page.id),
            )
        )
        self.assertRedirects(response, "/admin/")

    def test_cannot_create_page_when_can_create_at_returns_false(self):
        # issue #2892

        # Check that creating a second SingletonPage results in a permission
        # denied error.

        # SingletonPage overrides the can_create_at method to make it return
        # False if another SingletonPage already exists.

        # The Page model now has a max_count attribute (issue 4841),
        # but we are leaving this test in place to cover existing behaviour and
        # ensure it does not break any code doing this in the wild.
        add_url = reverse(
            "wagtailadmin_pages:add",
            args=[
                SingletonPage._meta.app_label,
                SingletonPage._meta.model_name,
                self.root_page.pk,
            ],
        )

        # A single singleton page should be creatable
        self.assertTrue(SingletonPage.can_create_at(self.root_page))
        response = self.client.get(add_url)
        self.assertEqual(response.status_code, 200)

        # Create a singleton page
        self.root_page.add_child(
            instance=SingletonPage(title="singleton", slug="singleton")
        )

        # A second singleton page should not be creatable
        self.assertFalse(SingletonPage.can_create_at(self.root_page))
        response = self.client.get(add_url)
        self.assertRedirects(response, "/admin/")

    def test_cannot_create_singleton_page_with_max_count(self):
        # Check that creating a second SingletonPageViaMaxCount results in a permission
        # denied error.

        # SingletonPageViaMaxCount uses the max_count attribute to limit the number of
        # instance it can have.

        add_url = reverse(
            "wagtailadmin_pages:add",
            args=[
                SingletonPageViaMaxCount._meta.app_label,
                SingletonPageViaMaxCount._meta.model_name,
                self.root_page.pk,
            ],
        )

        # A single singleton page should be creatable
        self.assertTrue(SingletonPageViaMaxCount.can_create_at(self.root_page))
        response = self.client.get(add_url)
        self.assertEqual(response.status_code, 200)

        # Create a singleton page
        self.root_page.add_child(
            instance=SingletonPageViaMaxCount(title="singleton", slug="singleton")
        )

        # A second singleton page should not be creatable
        self.assertFalse(SingletonPageViaMaxCount.can_create_at(self.root_page))
        response = self.client.get(add_url)
        self.assertRedirects(response, "/admin/")

    def test_cannot_create_page_with_wrong_parent_page_types(self):
        # tests.BusinessChild has limited parent_page_types, so attempting to add
        # a new one at the root level should fail with permission denied
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "businesschild", self.root_page.id),
            )
        )
        self.assertRedirects(response, "/admin/")

    def test_cannot_create_page_with_wrong_subpage_types(self):
        # Add a BusinessIndex to test business rules in
        business_index = BusinessIndex(
            title="Hello world!",
            slug="hello-world",
        )
        self.root_page.add_child(instance=business_index)

        # BusinessIndex has limited subpage_types, so attempting to add a SimplePage
        # underneath it should fail with permission denied
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "simplepage", business_index.id),
            )
        )
        self.assertRedirects(response, "/admin/")

    def test_create_simplepage_post(self):
        post_data = {
            "title": "New page!",
            "content": "Some content",
            "slug": "hello-world",
        }
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "simplepage", self.root_page.id),
            ),
            post_data,
        )

        # Find the page and check it
        page = Page.objects.get(
            path__startswith=self.root_page.path, slug="hello-world"
        ).specific

        # Should be redirected to edit page
        self.assertRedirects(
            response, reverse("wagtailadmin_pages:edit", args=(page.id,))
        )

        self.assertEqual(page.title, post_data["title"])
        self.assertEqual(page.draft_title, post_data["title"])
        self.assertIsInstance(page, SimplePage)
        self.assertFalse(page.live)
        self.assertFalse(page.first_published_at)

        # treebeard should report no consistency problems with the tree
        self.assertFalse(
            any(Page.find_problems()), "treebeard found consistency problems"
        )

    def test_create_simplepage_scheduled(self):
        go_live_at = timezone.now() + datetime.timedelta(days=1)
        expire_at = timezone.now() + datetime.timedelta(days=2)
        post_data = {
            "title": "New page!",
            "content": "Some content",
            "slug": "hello-world",
            "go_live_at": submittable_timestamp(go_live_at),
            "expire_at": submittable_timestamp(expire_at),
        }
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "simplepage", self.root_page.id),
            ),
            post_data,
        )

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        # Find the page and check the scheduled times
        page = Page.objects.get(
            path__startswith=self.root_page.path, slug="hello-world"
        ).specific
        self.assertEqual(page.go_live_at.date(), go_live_at.date())
        self.assertEqual(page.expire_at.date(), expire_at.date())
        self.assertIs(page.expired, False)
        self.assertTrue(page.status_string, "draft")

        # No revisions with approved_go_live_at
        self.assertFalse(
            PageRevision.objects.filter(page=page)
            .exclude(approved_go_live_at__isnull=True)
            .exists()
        )

    def test_create_simplepage_scheduled_go_live_before_expiry(self):
        post_data = {
            "title": "New page!",
            "content": "Some content",
            "slug": "hello-world",
            "go_live_at": submittable_timestamp(
                timezone.now() + datetime.timedelta(days=2)
            ),
            "expire_at": submittable_timestamp(
                timezone.now() + datetime.timedelta(days=1)
            ),
        }
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "simplepage", self.root_page.id),
            ),
            post_data,
        )

        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(
            response,
            "form",
            "go_live_at",
            "Go live date/time must be before expiry date/time",
        )
        self.assertFormError(
            response,
            "form",
            "expire_at",
            "Go live date/time must be before expiry date/time",
        )

        # form should be marked as having unsaved changes for the purposes of the dirty-forms warning
        self.assertContains(response, "alwaysDirty: true")

    def test_create_simplepage_scheduled_expire_in_the_past(self):
        post_data = {
            "title": "New page!",
            "content": "Some content",
            "slug": "hello-world",
            "expire_at": submittable_timestamp(
                timezone.now() + datetime.timedelta(days=-1)
            ),
        }
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "simplepage", self.root_page.id),
            ),
            post_data,
        )

        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(
            response, "form", "expire_at", "Expiry date/time must be in the future"
        )

        # form should be marked as having unsaved changes for the purposes of the dirty-forms warning
        self.assertContains(response, "alwaysDirty: true")

    def test_create_simplepage_post_publish(self):
        # Connect a mock signal handler to page_published signal
        mock_handler = mock.MagicMock()
        page_published.connect(mock_handler)

        # Post
        post_data = {
            "title": "New page!",
            "content": "Some content",
            "slug": "hello-world",
            "action-publish": "Publish",
        }
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "simplepage", self.root_page.id),
            ),
            post_data,
        )

        # Find the page and check it
        page = Page.objects.get(
            path__startswith=self.root_page.path, slug="hello-world"
        ).specific

        # Should be redirected to explorer
        self.assertRedirects(
            response, reverse("wagtailadmin_explore", args=(self.root_page.id,))
        )

        self.assertEqual(page.title, post_data["title"])
        self.assertEqual(page.draft_title, post_data["title"])
        self.assertIsInstance(page, SimplePage)
        self.assertTrue(page.live)
        self.assertTrue(page.first_published_at)

        # Check that the page_published signal was fired
        self.assertEqual(mock_handler.call_count, 1)
        mock_call = mock_handler.mock_calls[0][2]

        self.assertEqual(mock_call["sender"], page.specific_class)
        self.assertEqual(mock_call["instance"], page)
        self.assertIsInstance(mock_call["instance"], page.specific_class)

        # treebeard should report no consistency problems with the tree
        self.assertFalse(
            any(Page.find_problems()), "treebeard found consistency problems"
        )

    def test_create_simplepage_post_publish_scheduled(self):
        go_live_at = timezone.now() + datetime.timedelta(days=1)
        expire_at = timezone.now() + datetime.timedelta(days=2)
        post_data = {
            "title": "New page!",
            "content": "Some content",
            "slug": "hello-world",
            "action-publish": "Publish",
            "go_live_at": submittable_timestamp(go_live_at),
            "expire_at": submittable_timestamp(expire_at),
        }
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "simplepage", self.root_page.id),
            ),
            post_data,
        )

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        # Find the page and check it
        page = Page.objects.get(
            path__startswith=self.root_page.path, slug="hello-world"
        ).specific
        self.assertEqual(page.go_live_at.date(), go_live_at.date())
        self.assertEqual(page.expire_at.date(), expire_at.date())
        self.assertIs(page.expired, False)

        # A revision with approved_go_live_at should exist now
        self.assertTrue(
            PageRevision.objects.filter(page=page)
            .exclude(approved_go_live_at__isnull=True)
            .exists()
        )
        # But Page won't be live
        self.assertFalse(page.live)
        self.assertFalse(page.first_published_at)
        self.assertTrue(page.status_string, "scheduled")

    def test_create_simplepage_post_submit(self):
        # Create a moderator user for testing email
        self.create_superuser("moderator", "moderator@email.com", "password")

        # Submit
        post_data = {
            "title": "New page!",
            "content": "Some content",
            "slug": "hello-world",
            "action-submit": "Submit",
        }
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "simplepage", self.root_page.id),
            ),
            post_data,
        )

        # Find the page and check it
        page = Page.objects.get(
            path__startswith=self.root_page.path, slug="hello-world"
        ).specific

        # Should be redirected to explorer
        self.assertRedirects(
            response, reverse("wagtailadmin_explore", args=(self.root_page.id,))
        )

        self.assertEqual(page.title, post_data["title"])
        self.assertIsInstance(page, SimplePage)
        self.assertFalse(page.live)
        self.assertFalse(page.first_published_at)

        # The page should now be in moderation
        self.assertEqual(
            page.current_workflow_state.status,
            page.current_workflow_state.STATUS_IN_PROGRESS,
        )

    def test_create_simplepage_post_existing_slug(self):
        # This tests the existing slug checking on page save

        # Create a page
        self.child_page = SimplePage(
            title="Hello world!", slug="hello-world", content="hello"
        )
        self.root_page.add_child(instance=self.child_page)

        # Attempt to create a new one with the same slug
        post_data = {
            "title": "New page!",
            "content": "Some content",
            "slug": "hello-world",
            "action-publish": "Publish",
        }
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "simplepage", self.root_page.id),
            ),
            post_data,
        )

        # Should not be redirected (as the save should fail)
        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(response, "form", "slug", "This slug is already in use")

        # form should be marked as having unsaved changes for the purposes of the dirty-forms warning
        self.assertContains(response, "alwaysDirty: true")

    def test_create_nonexistantparent(self):
        response = self.client.get(
            reverse("wagtailadmin_pages:add", args=("tests", "simplepage", 100000))
        )
        self.assertEqual(response.status_code, 404)

    def test_create_nonpagetype(self):
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("wagtailimages", "image", self.root_page.id),
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_preview_on_create(self):
        post_data = {
            "title": "New page!",
            "content": "Some content",
            "slug": "hello-world",
            "action-submit": "Submit",
        }
        preview_url = reverse(
            "wagtailadmin_pages:preview_on_add",
            args=("tests", "simplepage", self.root_page.id),
        )
        response = self.client.post(preview_url, post_data)

        # Check the JSON response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode(), {"is_valid": True})

        response = self.client.get(preview_url)

        # Check the HTML response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tests/simple_page.html")
        self.assertContains(response, "New page!")

        # Check that the treebeard attributes were set correctly on the page object
        self.assertEqual(response.context["self"].depth, self.root_page.depth + 1)
        self.assertTrue(response.context["self"].path.startswith(self.root_page.path))
        self.assertEqual(response.context["self"].get_parent(), self.root_page)

    def test_whitespace_titles(self):
        post_data = {
            "title": " ",  # Single space on purpose
            "content": "Some content",
            "slug": "hello-world",
            "action-submit": "Submit",
        }
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "simplepage", self.root_page.id),
            ),
            post_data,
        )

        # Check that a form error was raised
        self.assertFormError(response, "form", "title", "This field is required.")

    def test_whitespace_titles_with_tab(self):
        post_data = {
            "title": "\t",  # Single space on purpose
            "content": "Some content",
            "slug": "hello-world",
            "action-submit": "Submit",
        }
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "simplepage", self.root_page.id),
            ),
            post_data,
        )

        # Check that a form error was raised
        self.assertFormError(response, "form", "title", "This field is required.")

    def test_whitespace_titles_with_tab_in_seo_title(self):
        post_data = {
            "title": "Hello",
            "content": "Some content",
            "slug": "hello-world",
            "action-submit": "Submit",
            "seo_title": "\t",
        }
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "simplepage", self.root_page.id),
            ),
            post_data,
        )

        # Should be successful, as seo_title is not required
        self.assertEqual(response.status_code, 302)

        # The tab should be automatically stripped from the seo_title
        page = Page.objects.order_by("-id").first()
        self.assertEqual(page.seo_title, "")

    def test_whitespace_is_stripped_from_titles(self):
        post_data = {
            "title": "   Hello   ",
            "content": "Some content",
            "slug": "hello-world",
            "action-submit": "Submit",
            "seo_title": "   hello SEO   ",
        }
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "simplepage", self.root_page.id),
            ),
            post_data,
        )

        # Should be successful, as both title and seo_title are non-empty after stripping
        self.assertEqual(response.status_code, 302)

        # Whitespace should be automatically stripped from title and seo_title
        page = Page.objects.order_by("-id").first()
        self.assertEqual(page.title, "Hello")
        self.assertEqual(page.draft_title, "Hello")
        self.assertEqual(page.seo_title, "hello SEO")

    def test_long_slug(self):
        post_data = {
            "title": "Hello world",
            "content": "Some content",
            "slug": "hello-world-hello-world-hello-world-hello-world-hello-world-hello-world-"
            "hello-world-hello-world-hello-world-hello-world-hello-world-hello-world-"
            "hello-world-hello-world-hello-world-hello-world-hello-world-hello-world-"
            "hello-world-hello-world-hello-world-hello-world-hello-world-hello-world",
            "action-submit": "Submit",
        }
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "simplepage", self.root_page.id),
            ),
            post_data,
        )

        # Check that a form error was raised
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response,
            "form",
            "slug",
            "Ensure this value has at most 255 characters (it has 287).",
        )

    def test_before_create_page_hook(self):
        def hook_func(request, parent_page, page_class):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(parent_page.id, self.root_page.id)
            self.assertEqual(page_class, SimplePage)

            return HttpResponse("Overridden!")

        with self.register_hook("before_create_page", hook_func):
            response = self.client.get(
                reverse(
                    "wagtailadmin_pages:add",
                    args=("tests", "simplepage", self.root_page.id),
                )
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

    def test_before_create_page_hook_post(self):
        def hook_func(request, parent_page, page_class):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(parent_page.id, self.root_page.id)
            self.assertEqual(page_class, SimplePage)

            return HttpResponse("Overridden!")

        with self.register_hook("before_create_page", hook_func):
            post_data = {
                "title": "New page!",
                "content": "Some content",
                "slug": "hello-world",
            }
            response = self.client.post(
                reverse(
                    "wagtailadmin_pages:add",
                    args=("tests", "simplepage", self.root_page.id),
                ),
                post_data,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # page should not be created
        self.assertFalse(Page.objects.filter(title="New page!").exists())

    def test_after_create_page_hook(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(page, SimplePage)

            # Both are None as this is only a draft
            self.assertIsNone(page.first_published_at)
            self.assertIsNone(page.last_published_at)

            return HttpResponse("Overridden!")

        with self.register_hook("after_create_page", hook_func):
            post_data = {
                "title": "New page!",
                "content": "Some content",
                "slug": "hello-world",
            }
            response = self.client.post(
                reverse(
                    "wagtailadmin_pages:add",
                    args=("tests", "simplepage", self.root_page.id),
                ),
                post_data,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # page should be created
        self.assertTrue(Page.objects.filter(title="New page!").exists())

    def test_after_create_page_hook_with_page_publish(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(page, SimplePage)

            self.assertIsNotNone(page.first_published_at)
            self.assertIsNotNone(page.last_published_at)

            return HttpResponse("Overridden!")

        with self.register_hook("after_create_page", hook_func):
            post_data = {
                "title": "New page!",
                "content": "Some content",
                "slug": "hello-world",
                "action-publish": "Publish",
            }
            response = self.client.post(
                reverse(
                    "wagtailadmin_pages:add",
                    args=("tests", "simplepage", self.root_page.id),
                ),
                post_data,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # page should be created
        self.assertTrue(Page.objects.filter(title="New page!").exists())

    def test_after_publish_page(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(page.title, "New page!")

            self.assertIsNotNone(page.first_published_at)
            self.assertIsNotNone(page.last_published_at)

            return HttpResponse("Overridden!")

        with self.register_hook("after_publish_page", hook_func):
            post_data = {
                "title": "New page!",
                "content": "Some content",
                "slug": "hello-world",
                "action-publish": "Publish",
            }
            response = self.client.post(
                reverse(
                    "wagtailadmin_pages:add",
                    args=("tests", "simplepage", self.root_page.id),
                ),
                post_data,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")
        self.root_page.refresh_from_db()
        self.assertEqual(self.root_page.get_children()[0].status_string, _("live"))

    def test_before_publish_page(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(page.title, "New page!")

            self.assertIsNone(page.first_published_at)
            self.assertIsNone(page.last_published_at)

            return HttpResponse("Overridden!")

        with self.register_hook("before_publish_page", hook_func):
            post_data = {
                "title": "New page!",
                "content": "Some content",
                "slug": "hello-world",
                "action-publish": "Publish",
            }
            response = self.client.post(
                reverse(
                    "wagtailadmin_pages:add",
                    args=("tests", "simplepage", self.root_page.id),
                ),
                post_data,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")
        self.root_page.refresh_from_db()
        self.assertEqual(
            self.root_page.get_children()[0].status_string, _("live + draft")
        )

    def test_display_moderation_button_by_default(self):
        """
        Tests that by default the "Submit for Moderation" button is shown in the action menu.
        """
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "simplepage", self.root_page.id),
            )
        )
        self.assertContains(
            response,
            '<button type="submit" name="action-submit" value="Submit for moderation" class="button">'
            '<svg class="icon icon-resubmit icon" aria-hidden="true"><use href="#icon-resubmit"></use></svg>'
            "Submit for moderation</button>",
        )

    @override_settings(WAGTAIL_MODERATION_ENABLED=False)
    def test_hide_moderation_button(self):
        """
        Tests that if WAGTAIL_MODERATION_ENABLED is set to False, the "Submit for Moderation" button is not shown.
        """
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "simplepage", self.root_page.id),
            )
        )
        self.assertNotContains(
            response,
            '<button type="submit" name="action-submit" value="Submit for moderation" class="button">Submit for moderation</button>',
        )

    def test_create_sets_locale_to_parent_locale(self):
        # We need to make sure the page's locale it set to the parent in the create view so that any customisations
        # for that language will take effect.
        fr_locale = Locale.objects.create(language_code="fr")
        fr_homepage = self.root_page.add_child(
            instance=Page(
                title="Home",
                slug="home-fr",
                locale=fr_locale,
            )
        )

        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add", args=("tests", "simplepage", fr_homepage.id)
            )
        )

        self.assertEqual(response.context["page"].locale, fr_locale)


class TestPermissionedFieldPanels(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)
        GroupPagePermission.objects.create(
            group=Group.objects.get(name="Site-wide editors"),
            page=self.root_page,
            permission_type="add",
        )

    def test_create_page_with_permissioned_field_panel(self):
        """
        Test that permission rules on field panels are honoured
        """
        # non-superusers should not see secret_data
        self.login(username="siteeditor", password="password")
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "secretpage", self.root_page.id),
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"boring_data"')
        self.assertNotContains(response, '"secret_data"')

        # superusers should see secret_data
        self.login(username="superuser", password="password")
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "secretpage", self.root_page.id),
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"boring_data"')
        self.assertContains(response, '"secret_data"')


class TestSubpageBusinessRules(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add standard page (allows subpages of any type)
        self.standard_index = StandardIndex()
        self.standard_index.title = "Standard Index"
        self.standard_index.slug = "standard-index"
        self.root_page.add_child(instance=self.standard_index)

        # Add business page (allows BusinessChild and BusinessSubIndex as subpages)
        self.business_index = BusinessIndex()
        self.business_index.title = "Business Index"
        self.business_index.slug = "business-index"
        self.root_page.add_child(instance=self.business_index)

        # Add business child (allows no subpages)
        self.business_child = BusinessChild()
        self.business_child.title = "Business Child"
        self.business_child.slug = "business-child"
        self.business_index.add_child(instance=self.business_child)

        # Add business subindex (allows only BusinessChild as subpages)
        self.business_subindex = BusinessSubIndex()
        self.business_subindex.title = "Business Subindex"
        self.business_subindex.slug = "business-subindex"
        self.business_index.add_child(instance=self.business_subindex)

        # Login
        self.login()

    def test_standard_subpage(self):
        add_subpage_url = reverse(
            "wagtailadmin_pages:add_subpage", args=(self.standard_index.id,)
        )

        # explorer should contain a link to 'add child page'
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.standard_index.id,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, add_subpage_url)

        # add_subpage should give us choices of StandardChild, and BusinessIndex.
        # BusinessSubIndex and BusinessChild are not allowed
        response = self.client.get(add_subpage_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, StandardChild.get_verbose_name())
        self.assertContains(response, BusinessIndex.get_verbose_name())
        self.assertNotContains(response, BusinessSubIndex.get_verbose_name())
        self.assertNotContains(response, BusinessChild.get_verbose_name())

    def test_business_subpage(self):
        add_subpage_url = reverse(
            "wagtailadmin_pages:add_subpage", args=(self.business_index.id,)
        )

        # explorer should contain a link to 'add child page'
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.business_index.id,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, add_subpage_url)

        # add_subpage should give us a cut-down set of page types to choose
        response = self.client.get(add_subpage_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, StandardIndex.get_verbose_name())
        self.assertNotContains(response, StandardChild.get_verbose_name())
        self.assertContains(response, BusinessSubIndex.get_verbose_name())
        self.assertContains(response, BusinessChild.get_verbose_name())

    def test_business_child_subpage(self):
        add_subpage_url = reverse(
            "wagtailadmin_pages:add_subpage", args=(self.business_child.id,)
        )

        # explorer should not contain a link to 'add child page', as this page doesn't accept subpages
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.business_child.id,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, add_subpage_url)

        # this also means that fetching add_subpage is blocked at the permission-check level
        response = self.client.get(
            reverse("wagtailadmin_pages:add_subpage", args=(self.business_child.id,))
        )
        self.assertEqual(response.status_code, 302)

    def test_cannot_add_invalid_subpage_type(self):
        # cannot add StandardChild as a child of BusinessIndex, as StandardChild is not present in subpage_types
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "standardchild", self.business_index.id),
            )
        )
        self.assertRedirects(response, "/admin/")

        # likewise for BusinessChild which has an empty subpage_types list
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "standardchild", self.business_child.id),
            )
        )
        self.assertRedirects(response, "/admin/")

        # cannot add BusinessChild to StandardIndex, as BusinessChild restricts is parent page types
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "businesschild", self.standard_index.id),
            )
        )
        self.assertRedirects(response, "/admin/")

        # but we can add a BusinessChild to BusinessIndex
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "businesschild", self.business_index.id),
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_not_prompted_for_page_type_when_only_one_choice(self):
        response = self.client.get(
            reverse("wagtailadmin_pages:add_subpage", args=(self.business_subindex.id,))
        )
        # BusinessChild is the only valid subpage type of BusinessSubIndex, so redirect straight there
        self.assertRedirects(
            response,
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "businesschild", self.business_subindex.id),
            ),
        )


class TestInlinePanelMedia(TestCase, WagtailTestUtils):
    """
    Test that form media required by InlinePanels is correctly pulled in to the edit page
    """

    def test_inline_panel_media(self):
        homepage = Page.objects.get(id=2)
        self.login()

        # simplepage does not need draftail...
        response = self.client.get(
            reverse("wagtailadmin_pages:add", args=("tests", "simplepage", homepage.id))
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "wagtailadmin/js/draftail.js")

        # but sectionedrichtextpage does
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "sectionedrichtextpage", homepage.id),
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "wagtailadmin/js/draftail.js")


class TestInlineStreamField(TestCase, WagtailTestUtils):
    """
    Test that streamfields inside an inline child work
    """

    def test_inline_streamfield(self):
        homepage = Page.objects.get(id=2)
        self.login()

        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "inlinestreampage", homepage.id),
            )
        )
        self.assertEqual(response.status_code, 200)

        # response should include HTML declarations for streamfield child blocks
        self.assertContains(response, '<div id="sections-__prefix__-body" data-block="')


class TestIssue2994(TestCase, WagtailTestUtils):
    """
    In contrast to most "standard" form fields, StreamField form widgets generally won't
    provide a postdata field with a name exactly matching the field name. To prevent Django
    from wrongly interpreting this as the field being omitted from the form,
    we need to provide a custom value_omitted_from_data method.
    """

    def setUp(self):
        self.root_page = Page.objects.get(id=2)
        self.user = self.login()

    def test_page_edit_post_publish_url(self):
        # Post
        post_data = {
            "title": "Issue 2994 test",
            "slug": "issue-2994-test",
            "body-count": "1",
            "body-0-deleted": "",
            "body-0-order": "0",
            "body-0-type": "text",
            "body-0-value": "hello world",
            "action-publish": "Publish",
        }
        self.client.post(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "defaultstreampage", self.root_page.id),
            ),
            post_data,
        )
        new_page = DefaultStreamPage.objects.get(slug="issue-2994-test")
        self.assertEqual(1, len(new_page.body))
        self.assertEqual("hello world", new_page.body[0].value)


class TestInlinePanelWithTags(TestCase, WagtailTestUtils):
    # https://github.com/wagtail/wagtail/issues/5414#issuecomment-567080707

    def setUp(self):
        self.root_page = Page.objects.get(id=2)
        self.user = self.login()

    def test_create(self):
        post_data = {
            "title": "Mr Benn",
            "slug": "mr-benn",
            "first_name": "William",
            "last_name": "Benn",
            "addresses-TOTAL_FORMS": 1,
            "addresses-INITIAL_FORMS": 0,
            "addresses-MIN_NUM_FORMS": 0,
            "addresses-MAX_NUM_FORMS": 1000,
            "addresses-0-address": "52 Festive Road, London",
            "addresses-0-tags": "shopkeeper, bowler-hat",
            "action-publish": "Publish",
            "comments-TOTAL_FORMS": 0,
            "comments-INITIAL_FORMS": 0,
            "comments-MIN_NUM_FORMS": 0,
            "comments-MAX_NUM_FORMS": 1000,
        }
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "personpage", self.root_page.id),
            ),
            post_data,
        )
        self.assertRedirects(
            response, reverse("wagtailadmin_explore", args=(self.root_page.id,))
        )
        new_page = PersonPage.objects.get(slug="mr-benn")
        self.assertEqual(new_page.addresses.first().tags.count(), 2)


class TestInlinePanelNonFieldErrors(TestCase, WagtailTestUtils):
    """
    Test that non field errors will render for InlinePanels
    https://github.com/wagtail/wagtail/issues/3890
    """

    fixtures = ["demosite.json"]

    def setUp(self):
        self.root_page = Page.objects.get(id=2)
        self.user = self.login()

    def test_create(self):
        post_data = {
            "title": "Issue 3890 test",
            "slug": "issue-3890-test",
            "related_links-TOTAL_FORMS": 1,
            "related_links-INITIAL_FORMS": 0,
            "related_links-MIN_NUM_FORMS": 0,
            "related_links-MAX_NUM_FORMS": 1000,
            "related_links-0-id": 0,
            "related_links-0-ORDER": 1,
            # Leaving all fields empty should raise a validation error
            "related_links-0-link_page": "",
            "related_links-0-link_document": "",
            "related_links-0-link_external": "",
            "carousel_items-INITIAL_FORMS": 0,
            "carousel_items-MAX_NUM_FORMS": 1000,
            "carousel_items-TOTAL_FORMS": 0,
            "action-publish": "Publish",
            "comments-TOTAL_FORMS": 0,
            "comments-INITIAL_FORMS": 0,
            "comments-MIN_NUM_FORMS": 0,
            "comments-MAX_NUM_FORMS": 1000,
        }
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:add",
                args=("demosite", "homepage", self.root_page.id),
            ),
            post_data,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "The page could not be created due to validation errors"
        )
        self.assertContains(
            response,
            "You must provide a related page, related document or an external URL",
            count=1,
        )


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestLocaleSelector(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        self.events_page = Page.objects.get(url_path="/home/events/")
        self.fr_locale = Locale.objects.create(language_code="fr")
        self.translated_events_page = self.events_page.copy_for_translation(
            self.fr_locale, copy_parents=True
        )
        self.user = self.login()

    @unittest.expectedFailure  # TODO: Page editor header rewrite
    def test_locale_selector(self):
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=["tests", "eventpage", self.events_page.id],
            )
        )

        self.assertContains(response, 'id="status-sidebar-english"')

        add_translation_url = reverse(
            "wagtailadmin_pages:add",
            args=["tests", "eventpage", self.translated_events_page.id],
        )
        self.assertContains(response, f'href="{add_translation_url}"')

    @override_settings(WAGTAIL_I18N_ENABLED=False)
    def test_locale_selector_not_present_when_i18n_disabled(self):
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=["tests", "eventpage", self.events_page.id],
            )
        )

        self.assertNotContains(response, "Page Locale:")

        add_translation_url = reverse(
            "wagtailadmin_pages:add",
            args=["tests", "eventpage", self.translated_events_page.id],
        )
        self.assertNotContains(response, f'href="{add_translation_url}"')

    def test_locale_selector_not_present_without_permission_to_add(self):
        # Remove user's permissions to add in the French tree
        group = Group.objects.get(name="Moderators")
        GroupPagePermission.objects.create(
            group=group,
            page=self.events_page,
            permission_type="add",
        )
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.groups.add(group)
        self.user.save()

        # Locale indicator should exist, but the "French" option should be hidden
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=["tests", "eventpage", self.events_page.id],
            )
        )

        self.assertContains(response, 'id="status-sidebar-english"')

        add_translation_url = reverse(
            "wagtailadmin_pages:add",
            args=["tests", "eventpage", self.translated_events_page.id],
        )
        self.assertNotContains(response, f'href="{add_translation_url}"')


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestLocaleSelectorOnRootPage(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        self.root_page = Page.objects.get(id=1)
        self.fr_locale = Locale.objects.create(language_code="fr")
        self.user = self.login()

    @unittest.expectedFailure  # TODO: Page editor header rewrite
    def test_locale_selector(self):
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=["demosite", "homepage", self.root_page.id],
            )
        )

        self.assertContains(response, 'id="status-sidebar-english"')

        add_translation_url = (
            reverse(
                "wagtailadmin_pages:add",
                args=["demosite", "homepage", self.root_page.id],
            )
            + "?locale=fr"
        )
        self.assertContains(response, f'href="{add_translation_url}"')

    @override_settings(WAGTAIL_I18N_ENABLED=False)
    def test_locale_selector_not_present_when_i18n_disabled(self):
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=["demosite", "homepage", self.root_page.id],
            )
        )

        self.assertNotContains(response, "Page Locale:")

        add_translation_url = (
            reverse(
                "wagtailadmin_pages:add",
                args=["demosite", "homepage", self.root_page.id],
            )
            + "?locale=fr"
        )
        self.assertNotContains(response, f'href="{add_translation_url}"')


class TestPageSubscriptionSettings(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Login
        self.user = self.login()

    def test_commment_notifications_switched_on_by_default(self):
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=["tests", "simplepage", self.root_page.id],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<input type="checkbox" name="comment_notifications" id="id_comment_notifications" checked>',
        )

    def test_post_with_comment_notifications_switched_on(self):
        post_data = {
            "title": "New page!",
            "content": "Some content",
            "slug": "hello-world",
            "comment_notifications": "on",
        }
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:add",
                args=["tests", "simplepage", self.root_page.id],
            ),
            post_data,
        )

        page = Page.objects.get(
            path__startswith=self.root_page.path, slug="hello-world"
        ).specific

        self.assertRedirects(
            response, reverse("wagtailadmin_pages:edit", args=[page.id])
        )

        # Check the subscription
        subscription = page.subscribers.get()

        self.assertEqual(subscription.user, self.user)
        self.assertTrue(subscription.comment_notifications)

    def test_post_with_comment_notifications_switched_off(self):
        post_data = {
            "title": "New page!",
            "content": "Some content",
            "slug": "hello-world",
        }
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:add",
                args=["tests", "simplepage", self.root_page.id],
            ),
            post_data,
        )

        page = Page.objects.get(
            path__startswith=self.root_page.path, slug="hello-world"
        ).specific

        self.assertRedirects(
            response, reverse("wagtailadmin_pages:edit", args=[page.id])
        )

        # Check the subscription
        subscription = page.subscribers.get()

        self.assertEqual(subscription.user, self.user)
        self.assertFalse(subscription.comment_notifications)
