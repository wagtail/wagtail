import datetime
import os

from unittest import mock

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core.files.base import ContentFile
from django.http import HttpRequest, HttpResponse
from django.test import TestCase, modify_settings, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from wagtail.admin.tests.pages.timestamps import submittable_timestamp
from wagtail.core.exceptions import PageClassNotFoundError
from wagtail.core.models import GroupPagePermission, Locale, Page, PageRevision, Site
from wagtail.core.signals import page_published
from wagtail.tests.testapp.models import (
    EVENT_AUDIENCE_CHOICES, Advert, AdvertPlacement, EventCategory, EventPage,
    EventPageCarouselItem, FilePage, ManyToManyBlogPage, SimplePage, SingleEventPage, StandardIndex,
    TaggedPage)
from wagtail.tests.utils import WagtailTestUtils
from wagtail.tests.utils.form_data import inline_formset, nested_form_data


class TestPageEdit(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add child page
        child_page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            content="hello",
        )
        self.root_page.add_child(instance=child_page)
        child_page.save_revision().publish()
        self.child_page = SimplePage.objects.get(id=child_page.id)

        # Add file page
        fake_file = ContentFile("File for testing multipart")
        fake_file.name = 'test.txt'
        file_page = FilePage(
            title="File Page",
            slug="file-page",
            file_field=fake_file,
        )
        self.root_page.add_child(instance=file_page)
        file_page.save_revision().publish()
        self.file_page = FilePage.objects.get(id=file_page.id)

        # Add event page (to test edit handlers)
        self.event_page = EventPage(
            title="Event page", slug="event-page",
            location='the moon', audience='public',
            cost='free', date_from='2001-01-01',
        )
        self.root_page.add_child(instance=self.event_page)

        # Add single event page (to test custom URL routes)
        self.single_event_page = SingleEventPage(
            title="Mars landing", slug="mars-landing",
            location='mars', audience='public',
            cost='free', date_from='2001-01-01',
        )
        self.root_page.add_child(instance=self.single_event_page)

        self.unpublished_page = SimplePage(
            title="Hello unpublished world!",
            slug="hello-unpublished-world",
            content="hello",
            live=False,
            has_unpublished_changes=True,
        )
        self.root_page.add_child(instance=self.unpublished_page)

        # Login
        self.user = self.login()

    def test_page_edit(self):
        # Tests that the edit page loads
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.event_page.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "text/html; charset=utf-8")
        self.assertContains(response, '<li class="header-meta--status">Published</li>', html=True)

        # Test InlinePanel labels/headings
        self.assertContains(response, '<legend>Speaker lineup</legend>')
        self.assertContains(response, 'Add speakers')

        # test register_page_action_menu_item hook
        self.assertContains(response,
                            '<button type="submit" name="action-panic" value="Panic!" class="button">Panic!</button>')
        self.assertContains(response, 'testapp/js/siren.js')

        # test construct_page_action_menu hook
        self.assertContains(response,
                            '<button type="submit" name="action-relax" value="Relax." class="button">Relax.</button>')

    def test_edit_draft_page_with_no_revisions(self):
        # Tests that the edit page loads
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.unpublished_page.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<li class="header-meta--status">Draft</li>', html=True)

    def test_edit_multipart(self):
        """
        Test checks if 'enctype="multipart/form-data"' is added and only to forms that require multipart encoding.
        """
        # check for SimplePage where is no file field
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.event_page.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'enctype="multipart/form-data"')
        self.assertTemplateUsed(response, 'wagtailadmin/pages/edit.html')

        # check for FilePage which has file field
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.file_page.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'enctype="multipart/form-data"')

    @mock.patch('wagtail.core.models.ContentType.model_class', return_value=None)
    def test_edit_when_specific_class_cannot_be_found(self, mocked_method):
        with self.assertRaises(PageClassNotFoundError):
            self.client.get(reverse('wagtailadmin_pages:edit', args=(self.event_page.id, )))

    def test_upload_file_publish(self):
        """
        Check that file uploads work when directly publishing
        """
        file_upload = ContentFile(b"A new file", name='published-file.txt')
        post_data = {
            'title': 'New file',
            'slug': 'new-file',
            'file_field': file_upload,
            'action-publish': "Publish",
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=[self.file_page.id]), post_data)

        # Should be redirected to explorer
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=[self.root_page.id]))

        # Check the new file exists
        file_page = FilePage.objects.get()

        self.assertEqual(file_page.file_field.name, file_upload.name)
        self.assertTrue(os.path.exists(file_page.file_field.path))
        self.assertEqual(file_page.file_field.read(), b"A new file")

    def test_upload_file_draft(self):
        """
        Check that file uploads work when saving a draft
        """
        file_upload = ContentFile(b"A new file", name='draft-file.txt')
        post_data = {
            'title': 'New file',
            'slug': 'new-file',
            'file_field': file_upload,
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=[self.file_page.id]), post_data)

        # Should be redirected to edit page
        self.assertRedirects(response, reverse('wagtailadmin_pages:edit', args=[self.file_page.id]))

        # Check the file was uploaded
        file_path = os.path.join(settings.MEDIA_ROOT, file_upload.name)
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, 'rb') as saved_file:
            self.assertEqual(saved_file.read(), b"A new file")

        # Publish the draft just created
        FilePage.objects.get().get_latest_revision().publish()

        # Get the file page, check the file is set
        file_page = FilePage.objects.get()
        self.assertEqual(file_page.file_field.name, file_upload.name)
        self.assertTrue(os.path.exists(file_page.file_field.path))
        self.assertEqual(file_page.file_field.read(), b"A new file")

    def test_page_edit_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        # Get edit page
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )))

        # Check that the user received a 302 redirected response
        self.assertEqual(response.status_code, 302)

    def test_page_edit_post(self):
        # Tests simple editing
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to edit page
        self.assertRedirects(response, reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )))

        # The page should have "has_unpublished_changes" flag set
        child_page_new = SimplePage.objects.get(id=self.child_page.id)
        self.assertTrue(child_page_new.has_unpublished_changes)

        # Page fields should not be changed (because we just created a new draft)
        self.assertEqual(child_page_new.title, self.child_page.title)
        self.assertEqual(child_page_new.content, self.child_page.content)
        self.assertEqual(child_page_new.slug, self.child_page.slug)

        # The draft_title should have a new title
        self.assertEqual(child_page_new.draft_title, post_data['title'])

    def test_page_edit_post_when_locked(self):
        # Tests that trying to edit a locked page results in an error

        # Lock the page
        self.child_page.locked = True
        self.child_page.save()

        # Post
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        # Shouldn't be redirected
        self.assertContains(response, "The page could not be saved as it is locked")

        # The page shouldn't have "has_unpublished_changes" flag set
        child_page_new = SimplePage.objects.get(id=self.child_page.id)
        self.assertFalse(child_page_new.has_unpublished_changes)

    def test_edit_post_scheduled(self):
        # put go_live_at and expire_at several days away from the current date, to avoid
        # false matches in content_json__contains tests
        go_live_at = timezone.now() + datetime.timedelta(days=10)
        expire_at = timezone.now() + datetime.timedelta(days=20)
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'go_live_at': submittable_timestamp(go_live_at),
            'expire_at': submittable_timestamp(expire_at),
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        child_page_new = SimplePage.objects.get(id=self.child_page.id)

        # The page will still be live
        self.assertTrue(child_page_new.live)

        # A revision with approved_go_live_at should not exist
        self.assertFalse(PageRevision.objects.filter(
            page=child_page_new).exclude(approved_go_live_at__isnull=True).exists()
        )

        # But a revision with go_live_at and expire_at in their content json *should* exist
        self.assertTrue(PageRevision.objects.filter(
            page=child_page_new, content_json__contains=str(go_live_at.date())).exists()
        )
        self.assertTrue(
            PageRevision.objects.filter(page=child_page_new, content_json__contains=str(expire_at.date())).exists()
        )

    def test_edit_scheduled_go_live_before_expiry(self):
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'go_live_at': submittable_timestamp(timezone.now() + datetime.timedelta(days=2)),
            'expire_at': submittable_timestamp(timezone.now() + datetime.timedelta(days=1)),
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(response, 'form', 'go_live_at', "Go live date/time must be before expiry date/time")
        self.assertFormError(response, 'form', 'expire_at', "Go live date/time must be before expiry date/time")

        # form should be marked as having unsaved changes for the purposes of the dirty-forms warning
        self.assertContains(response, "alwaysDirty: true")

    def test_edit_scheduled_expire_in_the_past(self):
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'expire_at': submittable_timestamp(timezone.now() + datetime.timedelta(days=-1)),
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(response, 'form', 'expire_at', "Expiry date/time must be in the future")

        # form should be marked as having unsaved changes for the purposes of the dirty-forms warning
        self.assertContains(response, "alwaysDirty: true")

    def test_page_edit_post_publish(self):
        # Connect a mock signal handler to page_published signal
        mock_handler = mock.MagicMock()
        page_published.connect(mock_handler)

        # Set has_unpublished_changes=True on the existing record to confirm that the publish action
        # is resetting it (and not just leaving it alone)
        self.child_page.has_unpublished_changes = True
        self.child_page.save()

        # Save current value of first_published_at so we can check that it doesn't change
        first_published_at = SimplePage.objects.get(id=self.child_page.id).first_published_at

        # Tests publish from edit page
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world-new',
            'action-publish': "Publish",
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data, follow=True
        )

        # Should be redirected to explorer
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page was edited
        child_page_new = SimplePage.objects.get(id=self.child_page.id)
        self.assertEqual(child_page_new.title, post_data['title'])
        self.assertEqual(child_page_new.draft_title, post_data['title'])

        # Check that the page_published signal was fired
        self.assertEqual(mock_handler.call_count, 1)
        mock_call = mock_handler.mock_calls[0][2]

        self.assertEqual(mock_call['sender'], child_page_new.specific_class)
        self.assertEqual(mock_call['instance'], child_page_new)
        self.assertIsInstance(mock_call['instance'], child_page_new.specific_class)

        # The page shouldn't have "has_unpublished_changes" flag set
        self.assertFalse(child_page_new.has_unpublished_changes)

        # first_published_at should not change as it was already set
        self.assertEqual(first_published_at, child_page_new.first_published_at)

        # The "View Live" button should have the updated slug.
        for message in response.context['messages']:
            self.assertIn('hello-world-new', message.message)
            break

    def test_first_published_at_editable(self):
        """Test that we can update the first_published_at via the Page edit form,
        for page models that expose it."""

        # Add child page, of a type which has first_published_at in its form
        child_page = ManyToManyBlogPage(
            title="Hello world!",
            slug="hello-again-world",
            body="hello",
        )
        self.root_page.add_child(instance=child_page)
        child_page.save_revision().publish()
        self.child_page = ManyToManyBlogPage.objects.get(id=child_page.id)

        initial_delta = self.child_page.first_published_at - timezone.now()

        first_published_at = timezone.now() - datetime.timedelta(days=2)

        post_data = {
            'title': "I've been edited!",
            'body': "Some content",
            'slug': 'hello-again-world',
            'action-publish': "Publish",
            'first_published_at': submittable_timestamp(first_published_at),
        }
        self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        # Get the edited page.
        child_page_new = ManyToManyBlogPage.objects.get(id=self.child_page.id)

        # first_published_at should have changed.
        new_delta = child_page_new.first_published_at - timezone.now()
        self.assertNotEqual(new_delta.days, initial_delta.days)
        # first_published_at should be 3 days ago.
        self.assertEqual(new_delta.days, -3)

    def test_edit_post_publish_scheduled_unpublished_page(self):
        # Unpublish the page
        self.child_page.live = False
        self.child_page.save()

        go_live_at = timezone.now() + datetime.timedelta(days=1)
        expire_at = timezone.now() + datetime.timedelta(days=2)
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-publish': "Publish",
            'go_live_at': submittable_timestamp(go_live_at),
            'expire_at': submittable_timestamp(expire_at),
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        child_page_new = SimplePage.objects.get(id=self.child_page.id)

        # The page should not be live anymore
        self.assertFalse(child_page_new.live)

        # Instead a revision with approved_go_live_at should now exist
        self.assertTrue(
            PageRevision.objects.filter(page=child_page_new).exclude(approved_go_live_at__isnull=True).exists()
        )

        # The page SHOULD have the "has_unpublished_changes" flag set,
        # because the changes are not visible as a live page yet
        self.assertTrue(
            child_page_new.has_unpublished_changes,
            "A page scheduled for future publishing should have has_unpublished_changes=True"
        )

        self.assertEqual(child_page_new.status_string, "scheduled")

    def test_edit_post_publish_now_an_already_scheduled_unpublished_page(self):
        # Unpublish the page
        self.child_page.live = False
        self.child_page.save()

        # First let's publish a page with a go_live_at in the future
        go_live_at = timezone.now() + datetime.timedelta(days=1)
        expire_at = timezone.now() + datetime.timedelta(days=2)
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-publish': "Publish",
            'go_live_at': submittable_timestamp(go_live_at),
            'expire_at': submittable_timestamp(expire_at),
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to edit page
        self.assertEqual(response.status_code, 302)

        child_page_new = SimplePage.objects.get(id=self.child_page.id)

        # The page should not be live
        self.assertFalse(child_page_new.live)

        self.assertEqual(child_page_new.status_string, "scheduled")

        # Instead a revision with approved_go_live_at should now exist
        self.assertTrue(
            PageRevision.objects.filter(page=child_page_new).exclude(approved_go_live_at__isnull=True).exists()
        )

        # Now, let's edit it and publish it right now
        go_live_at = timezone.now()
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-publish': "Publish",
            'go_live_at': "",
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to edit page
        self.assertEqual(response.status_code, 302)

        child_page_new = SimplePage.objects.get(id=self.child_page.id)

        # The page should be live now
        self.assertTrue(child_page_new.live)

        # And a revision with approved_go_live_at should not exist
        self.assertFalse(
            PageRevision.objects.filter(page=child_page_new).exclude(approved_go_live_at__isnull=True).exists()
        )

    def test_edit_post_publish_scheduled_published_page(self):
        # Page is live
        self.child_page.live = True
        self.child_page.save()

        live_revision = self.child_page.live_revision
        original_title = self.child_page.title

        go_live_at = timezone.now() + datetime.timedelta(days=1)
        expire_at = timezone.now() + datetime.timedelta(days=2)
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-publish': "Publish",
            'go_live_at': submittable_timestamp(go_live_at),
            'expire_at': submittable_timestamp(expire_at),
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        child_page_new = SimplePage.objects.get(id=self.child_page.id)

        # The page should still be live
        self.assertTrue(child_page_new.live)

        self.assertEqual(child_page_new.status_string, "live + scheduled")

        # Instead a revision with approved_go_live_at should now exist
        self.assertTrue(
            PageRevision.objects.filter(page=child_page_new).exclude(approved_go_live_at__isnull=True).exists()
        )

        # The page SHOULD have the "has_unpublished_changes" flag set,
        # because the changes are not visible as a live page yet
        self.assertTrue(
            child_page_new.has_unpublished_changes,
            "A page scheduled for future publishing should have has_unpublished_changes=True"
        )

        self.assertNotEqual(
            child_page_new.get_latest_revision(), live_revision,
            "A page scheduled for future publishing should have a new revision, that is not the live revision"
        )

        self.assertEqual(
            child_page_new.title, original_title,
            "A live page with scheduled revisions should still have original content"
        )

    def test_edit_post_publish_now_an_already_scheduled_published_page(self):
        # Unpublish the page
        self.child_page.live = True
        self.child_page.save()

        original_title = self.child_page.title
        # First let's publish a page with a go_live_at in the future
        go_live_at = timezone.now() + datetime.timedelta(days=1)
        expire_at = timezone.now() + datetime.timedelta(days=2)
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-publish': "Publish",
            'go_live_at': submittable_timestamp(go_live_at),
            'expire_at': submittable_timestamp(expire_at),
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to edit page
        self.assertEqual(response.status_code, 302)

        child_page_new = SimplePage.objects.get(id=self.child_page.id)

        # The page should still be live
        self.assertTrue(child_page_new.live)

        # Instead a revision with approved_go_live_at should now exist
        self.assertTrue(
            PageRevision.objects.filter(page=child_page_new).exclude(approved_go_live_at__isnull=True).exists()
        )

        self.assertEqual(
            child_page_new.title, original_title,
            "A live page with scheduled revisions should still have original content"
        )

        # Now, let's edit it and publish it right now
        go_live_at = timezone.now()
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-publish': "Publish",
            'go_live_at': "",
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to edit page
        self.assertEqual(response.status_code, 302)

        child_page_new = SimplePage.objects.get(id=self.child_page.id)

        # The page should be live now
        self.assertTrue(child_page_new.live)

        # And a revision with approved_go_live_at should not exist
        self.assertFalse(
            PageRevision.objects.filter(page=child_page_new).exclude(approved_go_live_at__isnull=True).exists()
        )

        self.assertEqual(
            child_page_new.title, post_data['title'],
            "A published page should have the new title"
        )

    def test_page_edit_post_submit(self):
        # Create a moderator user for testing email
        self.create_superuser('moderator', 'moderator@email.com', 'password')

        # Tests submitting from edit page
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-submit': "Submit",
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to explorer
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # The page should have "has_unpublished_changes" flag set
        child_page_new = SimplePage.objects.get(id=self.child_page.id)
        self.assertTrue(child_page_new.has_unpublished_changes)

        # The latest revision for the page should now be in moderation
        self.assertEqual(child_page_new.current_workflow_state.status, child_page_new.current_workflow_state.STATUS_IN_PROGRESS)

    def test_page_edit_post_existing_slug(self):
        # This tests the existing slug checking on page edit

        # Create a page
        self.child_page = SimplePage(title="Hello world 2", slug="hello-world2", content="hello")
        self.root_page.add_child(instance=self.child_page)

        # Attempt to change the slug to one thats already in use
        post_data = {
            'title': "Hello world 2",
            'slug': 'hello-world',
            'action-submit': "Submit",
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        # Should not be redirected (as the save should fail)
        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(response, 'form', 'slug', "This slug is already in use")

    def test_preview_on_edit(self):
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-submit': "Submit",
        }
        preview_url = reverse('wagtailadmin_pages:preview_on_edit',
                              args=(self.child_page.id,))
        response = self.client.post(preview_url, post_data)

        # Check the JSON response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode(), {'is_valid': True})

        response = self.client.get(preview_url)

        # Check the HTML response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tests/simple_page.html')
        self.assertContains(response, "I&#39;ve been edited!", html=True)

    def test_preview_on_edit_no_session_key(self):
        preview_url = reverse('wagtailadmin_pages:preview_on_edit',
                              args=(self.child_page.id,))

        # get() without corresponding post(), key not set.
        response = self.client.get(preview_url)

        # Check the HTML response
        self.assertEqual(response.status_code, 200)

        # We should have an error page because we are unable to
        # preview; the page key was not in the session.
        self.assertContains(
            response,
            "<title>Wagtail - Preview error</title>",
            html=True
        )
        self.assertContains(
            response,
            "<h1>Preview error</h1>",
            html=True
        )

    @override_settings(CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }})
    @modify_settings(MIDDLEWARE={
        'append': 'django.middleware.cache.FetchFromCacheMiddleware',
        'prepend': 'django.middleware.cache.UpdateCacheMiddleware',
    })
    def test_preview_does_not_cache(self):
        '''
        Tests solution to issue #5975
        '''
        post_data = {
            'title': "I've been edited one time!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-submit': "Submit",
        }
        preview_url = reverse('wagtailadmin_pages:preview_on_edit',
                              args=(self.child_page.id,))
        self.client.post(preview_url, post_data)
        response = self.client.get(preview_url)
        self.assertContains(response, "I&#39;ve been edited one time!", html=True)

        post_data['title'] = "I've been edited two times!"
        self.client.post(preview_url, post_data)
        response = self.client.get(preview_url)
        self.assertContains(response, "I&#39;ve been edited two times!", html=True)

    @modify_settings(ALLOWED_HOSTS={'append': 'childpage.example.com'})
    def test_preview_uses_correct_site(self):
        # create a Site record for the child page
        Site.objects.create(hostname='childpage.example.com', root_page=self.child_page)

        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-submit': "Submit",
        }
        preview_url = reverse('wagtailadmin_pages:preview_on_edit',
                              args=(self.child_page.id,))
        response = self.client.post(preview_url, post_data)

        # Check the JSON response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode(), {'is_valid': True})

        response = self.client.get(preview_url)

        # Check that the correct site object has been selected by the site middleware
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tests/simple_page.html')
        self.assertEqual(Site.find_for_request(response.context['request']).hostname, 'childpage.example.com')

    def test_editor_picks_up_direct_model_edits(self):
        # If a page has no draft edits, the editor should show the version from the live database
        # record rather than the latest revision record. This ensures that the edit interface
        # reflects any changes made directly on the model.
        self.child_page.title = "This title only exists on the live database record"
        self.child_page.save()

        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This title only exists on the live database record")

    def test_editor_does_not_pick_up_direct_model_edits_when_draft_edits_exist(self):
        # If a page has draft edits, we should always show those in the editor, not the live
        # database record
        self.child_page.content = "Some content with a draft edit"
        self.child_page.save_revision()

        # make an independent change to the live database record
        self.child_page = SimplePage.objects.get(id=self.child_page.id)
        self.child_page.title = "This title only exists on the live database record"
        self.child_page.save()

        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "This title only exists on the live database record")
        self.assertContains(response, "Some content with a draft edit")

    def test_editor_page_shows_live_url_in_status_when_draft_edits_exist(self):
        # If a page has draft edits (ie. page has unpublished changes)
        # that affect the URL (eg. slug) we  should still ensure the
        # status button at the top of the page links to the live URL

        self.child_page.content = "Some content with a draft edit"
        self.child_page.slug = "revised-slug-in-draft-only"  # live version contains 'hello-world'
        self.child_page.save_revision()

        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )))

        link_to_live = '<a href="/hello-world/" target="_blank" rel="noopener noreferrer" class="button button-nostroke button--live" title="Visit the live page">\n' \
                       '<svg class="icon icon-link-external initial" aria-hidden="true" focusable="false"><use href="#icon-link-external"></use></svg>\n\n        ' \
                       'Live\n        <span class="privacy-indicator-tag u-hidden" aria-hidden="true" title="This page is live but only available to certain users">(restricted)</span>'
        input_field_for_draft_slug = '<input type="text" name="slug" value="revised-slug-in-draft-only" id="id_slug" maxlength="255" required />'
        input_field_for_live_slug = '<input type="text" name="slug" value="hello-world" id="id_slug" maxlength="255" required />'

        # Status Link should be the live page (not revision)
        self.assertContains(response, link_to_live, html=True)
        self.assertNotContains(response, 'href="/revised-slug-in-draft-only/"', html=True)

        # Editing input for slug should be the draft revision
        self.assertContains(response, input_field_for_draft_slug, html=True)
        self.assertNotContains(response, input_field_for_live_slug, html=True)

    def test_editor_page_shows_custom_live_url_in_status_when_draft_edits_exist(self):
        # When showing a live URL in the status button that differs from the draft one,
        # ensure that we pick up any custom URL logic defined on the specific page model

        self.single_event_page.location = "The other side of Mars"
        self.single_event_page.slug = "revised-slug-in-draft-only"  # live version contains 'hello-world'
        self.single_event_page.save_revision()

        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.single_event_page.id, )))

        link_to_live = '<a href="/mars-landing/pointless-suffix/" target="_blank" rel="noopener noreferrer" class="button button-nostroke button--live" title="Visit the live page">\n' \
                       '<svg class="icon icon-link-external initial" aria-hidden="true" focusable="false"><use href="#icon-link-external"></use></svg>\n\n        ' \
                       'Live\n        <span class="privacy-indicator-tag u-hidden" aria-hidden="true" title="This page is live but only available to certain users">(restricted)</span>'
        input_field_for_draft_slug = '<input type="text" name="slug" value="revised-slug-in-draft-only" id="id_slug" maxlength="255" required />'
        input_field_for_live_slug = '<input type="text" name="slug" value="mars-landing" id="id_slug" maxlength="255" required />'

        # Status Link should be the live page (not revision)
        self.assertContains(response, link_to_live, html=True)
        self.assertNotContains(response, 'href="/revised-slug-in-draft-only/pointless-suffix/"', html=True)

        # Editing input for slug should be the draft revision
        self.assertContains(response, input_field_for_draft_slug, html=True)
        self.assertNotContains(response, input_field_for_live_slug, html=True)

    def test_before_edit_page_hook(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(page.id, self.child_page.id)

            return HttpResponse("Overridden!")

        with self.register_hook('before_edit_page', hook_func):
            response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

    def test_before_edit_page_hook_post(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(page.id, self.child_page.id)

            return HttpResponse("Overridden!")

        with self.register_hook('before_edit_page', hook_func):
            post_data = {
                'title': "I've been edited!",
                'content': "Some content",
                'slug': 'hello-world-new',
                'action-publish': "Publish",
            }
            response = self.client.post(
                reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # page should not be edited
        self.assertEqual(Page.objects.get(id=self.child_page.id).title, "Hello world!")

    def test_after_edit_page_hook(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(page.id, self.child_page.id)

            return HttpResponse("Overridden!")

        with self.register_hook('after_edit_page', hook_func):
            post_data = {
                'title': "I've been edited!",
                'content': "Some content",
                'slug': 'hello-world-new',
                'action-publish': "Publish",
            }
            response = self.client.post(
                reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # page should be edited
        self.assertEqual(Page.objects.get(id=self.child_page.id).title, "I've been edited!")

    def test_after_publish_page(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(page.id, self.child_page.id)

            return HttpResponse("Overridden!")

        with self.register_hook("after_publish_page", hook_func):
            post_data = {
                'title': "I've been edited!",
                'content': "Some content",
                'slug': 'hello-world-new',
                'action-publish': "Publish",
            }
            response = self.client.post(
                reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")
        self.child_page.refresh_from_db()
        self.assertEqual(self.child_page.status_string, _("live"))

    def test_before_publish_page(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(page.id, self.child_page.id)

            return HttpResponse("Overridden!")

        with self.register_hook("before_publish_page", hook_func):
            post_data = {
                'title': "I've been edited!",
                'content': "Some content",
                'slug': 'hello-world-new',
                'action-publish': "Publish",
            }
            response = self.client.post(
                reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")
        self.child_page.refresh_from_db()
        self.assertEqual(self.child_page.status_string, _("live + draft"))

    def test_override_default_action_menu_item(self):
        def hook_func(menu_items, request, context):
            for (index, item) in enumerate(menu_items):
                if item.name == 'action-publish':
                    # move to top of list
                    menu_items.pop(index)
                    menu_items.insert(0, item)
                    break

        with self.register_hook('construct_page_action_menu', hook_func):
            response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.single_event_page.id, )))

        publish_button = '''
            <button type="submit" name="action-publish" value="action-publish" class="button button-longrunning " data-clicked-text="Publishing…">
                <svg class="icon icon-upload button-longrunning__icon" aria-hidden="true" focusable="false"><use href="#icon-upload"></use></svg>

                <svg class="icon icon-spinner icon" aria-hidden="true" focusable="false"><use href="#icon-spinner"></use></svg><em>Publish</em>
            </button>
        '''
        save_button = '''
            <button type="submit" class="button action-save button-longrunning " data-clicked-text="Saving…" >
                <svg class="icon icon-draft button-longrunning__icon" aria-hidden="true" focusable="false"><use href="#icon-draft"></use></svg>

                <svg class="icon icon-spinner icon" aria-hidden="true" focusable="false"><use href="#icon-spinner"></use></svg>
                <em>Save draft</em>
            </button>
        '''

        # save button should be in a <li>
        self.assertContains(response, "<li>%s</li>" % save_button, html=True)

        # publish button should be present, but not in a <li>
        self.assertContains(response, publish_button, html=True)
        self.assertNotContains(response, "<li>%s</li>" % publish_button, html=True)

    def test_edit_alias_page(self):
        alias_page = self.event_page.create_alias(update_slug='new-event-page')
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=[alias_page.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "text/html; charset=utf-8")

        # Should still have status in the header
        self.assertContains(response, '<li class="header-meta--status">Published</li>', html=True)

        # Check the edit_alias.html template was used instead
        self.assertTemplateUsed(response, 'wagtailadmin/pages/edit_alias.html')
        original_page_edit_url = reverse('wagtailadmin_pages:edit', args=[self.event_page.id])
        self.assertContains(response, f'<a class="button button-secondary" href="{original_page_edit_url}">Edit original page</a>', html=True)

    def test_post_edit_alias_page(self):
        alias_page = self.child_page.create_alias(update_slug='new-child-page')

        # Tests simple editing
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=[alias_page.id]), post_data)

        self.assertEqual(response.status_code, 405)

    def test_edit_after_change_language_code(self):
        """
        Verify that changing LANGUAGE_CODE with no corresponding database change does not break editing
        """
        # Add a draft revision
        self.child_page.title = "Hello world updated"
        self.child_page.save_revision()

        # Hack the Locale model to simulate a page tree that was created with LANGUAGE_CODE = 'de'
        # (which is not a valid content language under the current configuration)
        Locale.objects.update(language_code='de')

        # Tests that the edit page loads
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )))
        self.assertEqual(response.status_code, 200)

        # Tests simple editing
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to edit page
        self.assertRedirects(response, reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )))

    def test_edit_after_change_language_code_without_revisions(self):
        """
        Verify that changing LANGUAGE_CODE with no corresponding database change does not break editing
        """
        # Hack the Locale model to simulate a page tree that was created with LANGUAGE_CODE = 'de'
        # (which is not a valid content language under the current configuration)
        Locale.objects.update(language_code='de')

        PageRevision.objects.filter(page_id=self.child_page.id).delete()

        # Tests that the edit page loads
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )))
        self.assertEqual(response.status_code, 200)

        # Tests simple editing
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to edit page
        self.assertRedirects(response, reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )))


class TestPageEditReordering(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add event page
        self.event_page = EventPage(
            title="Event page", slug="event-page",
            location='the moon', audience='public',
            cost='free', date_from='2001-01-01',
        )
        self.event_page.carousel_items = [
            EventPageCarouselItem(caption='1234567', sort_order=1),
            EventPageCarouselItem(caption='7654321', sort_order=2),
            EventPageCarouselItem(caption='abcdefg', sort_order=3),
        ]
        self.root_page.add_child(instance=self.event_page)

        # Login
        self.user = self.login()

    def check_order(self, response, expected_order):
        inline_panel = response.context['edit_handler'].children[0].children[9]
        order = [child.form.instance.caption for child in inline_panel.children]
        self.assertEqual(order, expected_order)

    def test_order(self):
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.event_page.id, )))

        self.assertEqual(response.status_code, 200)
        self.check_order(response, ['1234567', '7654321', 'abcdefg'])

    def test_reorder(self):
        post_data = {
            'title': "Event page",
            'slug': 'event-page',

            'date_from': '01/01/2014',
            'cost': '$10',
            'audience': 'public',
            'location': 'somewhere',

            'related_links-INITIAL_FORMS': 0,
            'related_links-MAX_NUM_FORMS': 1000,
            'related_links-TOTAL_FORMS': 0,

            'speakers-INITIAL_FORMS': 0,
            'speakers-MAX_NUM_FORMS': 1000,
            'speakers-TOTAL_FORMS': 0,

            'head_counts-INITIAL_FORMS': 0,
            'head_counts-MAX_NUM_FORMS': 1000,
            'head_counts-TOTAL_FORMS': 0,

            'carousel_items-INITIAL_FORMS': 3,
            'carousel_items-MAX_NUM_FORMS': 1000,
            'carousel_items-TOTAL_FORMS': 3,
            'carousel_items-0-id': self.event_page.carousel_items.all()[0].id,
            'carousel_items-0-caption': self.event_page.carousel_items.all()[0].caption,
            'carousel_items-0-ORDER': 2,
            'carousel_items-1-id': self.event_page.carousel_items.all()[1].id,
            'carousel_items-1-caption': self.event_page.carousel_items.all()[1].caption,
            'carousel_items-1-ORDER': 3,
            'carousel_items-2-id': self.event_page.carousel_items.all()[2].id,
            'carousel_items-2-caption': self.event_page.carousel_items.all()[2].caption,
            'carousel_items-2-ORDER': 1,
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.event_page.id, )), post_data)

        # Should be redirected back to same page
        self.assertRedirects(response, reverse('wagtailadmin_pages:edit', args=(self.event_page.id, )))

        # Check order
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.event_page.id, )))

        self.assertEqual(response.status_code, 200)
        self.check_order(response, ['abcdefg', '1234567', '7654321'])

    def test_reorder_with_validation_error(self):
        post_data = {
            'title': "",  # Validation error
            'slug': 'event-page',

            'date_from': '01/01/2014',
            'cost': '$10',
            'audience': 'public',
            'location': 'somewhere',

            'related_links-INITIAL_FORMS': 0,
            'related_links-MAX_NUM_FORMS': 1000,
            'related_links-TOTAL_FORMS': 0,

            'speakers-INITIAL_FORMS': 0,
            'speakers-MAX_NUM_FORMS': 1000,
            'speakers-TOTAL_FORMS': 0,

            'head_counts-INITIAL_FORMS': 0,
            'head_counts-MAX_NUM_FORMS': 1000,
            'head_counts-TOTAL_FORMS': 0,

            'carousel_items-INITIAL_FORMS': 3,
            'carousel_items-MAX_NUM_FORMS': 1000,
            'carousel_items-TOTAL_FORMS': 3,
            'carousel_items-0-id': self.event_page.carousel_items.all()[0].id,
            'carousel_items-0-caption': self.event_page.carousel_items.all()[0].caption,
            'carousel_items-0-ORDER': 2,
            'carousel_items-1-id': self.event_page.carousel_items.all()[1].id,
            'carousel_items-1-caption': self.event_page.carousel_items.all()[1].caption,
            'carousel_items-1-ORDER': 3,
            'carousel_items-2-id': self.event_page.carousel_items.all()[2].id,
            'carousel_items-2-caption': self.event_page.carousel_items.all()[2].caption,
            'carousel_items-2-ORDER': 1,
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.event_page.id, )), post_data)

        self.assertEqual(response.status_code, 200)
        self.check_order(response, ['abcdefg', '1234567', '7654321'])


class TestIssue197(TestCase, WagtailTestUtils):
    def test_issue_197(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Create a tagged page with no tags
        self.tagged_page = self.root_page.add_child(instance=TaggedPage(
            title="Tagged page",
            slug='tagged-page',
            live=False,
        ))

        # Login
        self.user = self.login()

        # Add some tags and publish using edit view
        post_data = {
            'title': "Tagged page",
            'slug': 'tagged-page',
            'tags': "hello, world",
            'action-publish': "Publish",
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.tagged_page.id, )), post_data)

        # Should be redirected to explorer
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that both tags are in the pages tag set
        page = TaggedPage.objects.get(id=self.tagged_page.id)
        self.assertIn('hello', page.tags.slugs())
        self.assertIn('world', page.tags.slugs())


class TestChildRelationsOnSuperclass(TestCase, WagtailTestUtils):
    # In our test models we define AdvertPlacement as a child relation on the Page model.
    # Here we check that this behaves correctly when exposed on the edit form of a Page
    # subclass (StandardIndex here).
    fixtures = ['test.json']

    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)
        self.test_advert = Advert.objects.get(id=1)

        # Add child page
        self.index_page = StandardIndex(
            title="My lovely index",
            slug="my-lovely-index",
            advert_placements=[AdvertPlacement(advert=self.test_advert)]
        )
        self.root_page.add_child(instance=self.index_page)

        # Login
        self.login()

    def test_get_create_form(self):
        response = self.client.get(
            reverse('wagtailadmin_pages:add', args=('tests', 'standardindex', self.root_page.id))
        )
        self.assertEqual(response.status_code, 200)
        # Response should include an advert_placements formset labelled Adverts
        self.assertContains(response, "Adverts")
        self.assertContains(response, "id_advert_placements-TOTAL_FORMS")

    def test_post_create_form(self):
        post_data = {
            'title': "New index!",
            'slug': 'new-index',
            'advert_placements-TOTAL_FORMS': '1',
            'advert_placements-INITIAL_FORMS': '0',
            'advert_placements-MAX_NUM_FORMS': '1000',
            'advert_placements-0-advert': '1',
            'advert_placements-0-colour': 'yellow',
            'advert_placements-0-id': '',
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:add', args=('tests', 'standardindex', self.root_page.id)), post_data
        )

        # Find the page and check it
        page = Page.objects.get(path__startswith=self.root_page.path, slug='new-index').specific

        # Should be redirected to edit page
        self.assertRedirects(response, reverse('wagtailadmin_pages:edit', args=(page.id, )))

        self.assertEqual(page.advert_placements.count(), 1)
        self.assertEqual(page.advert_placements.first().advert.text, 'test_advert')

    def test_post_create_form_with_validation_error_in_formset(self):
        post_data = {
            'title': "New index!",
            'slug': 'new-index',
            'advert_placements-TOTAL_FORMS': '1',
            'advert_placements-INITIAL_FORMS': '0',
            'advert_placements-MAX_NUM_FORMS': '1000',
            'advert_placements-0-advert': '1',
            'advert_placements-0-colour': '',  # should fail as colour is a required field
            'advert_placements-0-id': '',
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:add', args=('tests', 'standardindex', self.root_page.id)), post_data
        )

        # Should remain on the edit page with a validation error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")
        # form should be marked as having unsaved changes
        self.assertContains(response, "alwaysDirty: true")

    def test_get_edit_form(self):
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.index_page.id, )))
        self.assertEqual(response.status_code, 200)

        # Response should include an advert_placements formset labelled Adverts
        self.assertContains(response, "Adverts")
        self.assertContains(response, "id_advert_placements-TOTAL_FORMS")
        # the formset should be populated with an existing form
        self.assertContains(response, "id_advert_placements-0-advert")
        self.assertContains(
            response, '<option value="1" selected="selected">test_advert</option>', html=True
        )

    def test_post_edit_form(self):
        post_data = {
            'title': "My lovely index",
            'slug': 'my-lovely-index',
            'advert_placements-TOTAL_FORMS': '2',
            'advert_placements-INITIAL_FORMS': '1',
            'advert_placements-MAX_NUM_FORMS': '1000',
            'advert_placements-0-advert': '1',
            'advert_placements-0-colour': 'yellow',
            'advert_placements-0-id': self.index_page.advert_placements.first().id,
            'advert_placements-1-advert': '1',
            'advert_placements-1-colour': 'purple',
            'advert_placements-1-id': '',
            'action-publish': "Publish",
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.index_page.id, )), post_data)

        # Should be redirected to explorer
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Find the page and check it
        page = Page.objects.get(id=self.index_page.id).specific
        self.assertEqual(page.advert_placements.count(), 2)
        self.assertEqual(page.advert_placements.all()[0].advert.text, 'test_advert')
        self.assertEqual(page.advert_placements.all()[1].advert.text, 'test_advert')

    def test_post_edit_form_with_validation_error_in_formset(self):
        post_data = {
            'title': "My lovely index",
            'slug': 'my-lovely-index',
            'advert_placements-TOTAL_FORMS': '1',
            'advert_placements-INITIAL_FORMS': '1',
            'advert_placements-MAX_NUM_FORMS': '1000',
            'advert_placements-0-advert': '1',
            'advert_placements-0-colour': '',
            'advert_placements-0-id': self.index_page.advert_placements.first().id,
            'action-publish': "Publish",
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.index_page.id, )), post_data)

        # Should remain on the edit page with a validation error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")
        # form should be marked as having unsaved changes
        self.assertContains(response, "alwaysDirty: true")


class TestIssue2492(TestCase, WagtailTestUtils):
    """
    The publication submission message generation was performed using
    the Page class, as opposed to the specific_class for that Page.
    This test ensures that the specific_class url method is called
    when the 'view live' message button is created.
    """

    def setUp(self):
        self.root_page = Page.objects.get(id=2)
        child_page = SingleEventPage(
            title="Test Event", slug="test-event", location="test location",
            cost="10", date_from=datetime.datetime.now(),
            audience=EVENT_AUDIENCE_CHOICES[0][0])
        self.root_page.add_child(instance=child_page)
        child_page.save_revision().publish()
        self.child_page = SingleEventPage.objects.get(id=child_page.id)
        self.user = self.login()

    def test_page_edit_post_publish_url(self):
        post_data = {
            'action-publish': "Publish",
            'title': self.child_page.title,
            'date_from': self.child_page.date_from,
            'slug': self.child_page.slug,
            'audience': self.child_page.audience,
            'location': self.child_page.location,
            'cost': self.child_page.cost,
            'carousel_items-TOTAL_FORMS': 0,
            'carousel_items-INITIAL_FORMS': 0,
            'carousel_items-MIN_NUM_FORMS': 0,
            'carousel_items-MAX_NUM_FORMS': 0,
            'speakers-TOTAL_FORMS': 0,
            'speakers-INITIAL_FORMS': 0,
            'speakers-MIN_NUM_FORMS': 0,
            'speakers-MAX_NUM_FORMS': 0,
            'related_links-TOTAL_FORMS': 0,
            'related_links-INITIAL_FORMS': 0,
            'related_links-MIN_NUM_FORMS': 0,
            'related_links-MAX_NUM_FORMS': 0,
            'head_counts-TOTAL_FORMS': 0,
            'head_counts-INITIAL_FORMS': 0,
            'head_counts-MIN_NUM_FORMS': 0,
            'head_counts-MAX_NUM_FORMS': 0,
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )),
            post_data, follow=True)

        # Grab a fresh copy's URL
        new_url = SingleEventPage.objects.get(id=self.child_page.id).url

        # The "View Live" button should have the custom URL.
        for message in response.context['messages']:
            self.assertIn('"{}"'.format(new_url), message.message)
            break


class TestIssue3982(TestCase, WagtailTestUtils):
    """
    Pages that are not associated with a site, and thus do not have a live URL,
    should not display a "View live" link in the flash message after being
    edited.
    """

    def setUp(self):
        super().setUp()
        self.login()

    def _create_page(self, parent):
        response = self.client.post(
            reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', parent.pk)),
            {'title': "Hello, world!", 'content': "Some content", 'slug': 'hello-world', 'action-publish': "publish"},
            follow=True)
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(parent.pk,)))
        page = SimplePage.objects.get()
        self.assertTrue(page.live)
        return response, page

    def test_create_accessible(self):
        """
        Create a page under the site root, check the flash message has a valid
        "View live" button.
        """
        response, page = self._create_page(Page.objects.get(pk=2))
        self.assertIsNotNone(page.url)
        self.assertTrue(any(
            'View live' in message.message and page.url in message.message
            for message in response.context['messages']))

    def test_create_inaccessible(self):
        """
        Create a page outside of the site root, check the flash message does
        not have a "View live" button.
        """
        response, page = self._create_page(Page.objects.get(pk=1))
        self.assertIsNone(page.url)
        self.assertFalse(any(
            'View live' in message.message
            for message in response.context['messages']))

    def _edit_page(self, parent):
        page = parent.add_child(instance=SimplePage(title='Hello, world!', content='Some content'))
        response = self.client.post(
            reverse('wagtailadmin_pages:edit', args=(page.pk,)),
            {'title': "Hello, world!", 'content': "Some content", 'slug': 'hello-world', 'action-publish': "publish"},
            follow=True)
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(parent.pk,)))
        page = SimplePage.objects.get(pk=page.pk)
        self.assertTrue(page.live)
        return response, page

    def test_edit_accessible(self):
        """
        Edit a page under the site root, check the flash message has a valid
        "View live" button.
        """
        response, page = self._edit_page(Page.objects.get(pk=2))
        self.assertIsNotNone(page.url)
        self.assertTrue(any(
            'View live' in message.message and page.url in message.message
            for message in response.context['messages']))

    def test_edit_inaccessible(self):
        """
        Edit a page outside of the site root, check the flash message does
        not have a "View live" button.
        """
        response, page = self._edit_page(Page.objects.get(pk=1))
        self.assertIsNone(page.url)
        self.assertFalse(any(
            'View live' in message.message
            for message in response.context['messages']))

    def _approve_page(self, parent):
        response = self.client.post(
            reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', parent.pk)),
            {'title': "Hello, world!", 'content': "Some content", 'slug': 'hello-world'},
            follow=True)
        page = SimplePage.objects.get()
        self.assertFalse(page.live)
        revision = PageRevision.objects.get(page=page)
        revision.submitted_for_moderation = True
        revision.save()
        response = self.client.post(reverse('wagtailadmin_pages:approve_moderation', args=(revision.pk,)), follow=True)
        page = SimplePage.objects.get()
        self.assertTrue(page.live)
        self.assertRedirects(response, reverse('wagtailadmin_home'))
        return response, page

    def test_approve_accessible(self):
        """
        Edit a page under the site root, check the flash message has a valid
        "View live" button.
        """
        response, page = self._approve_page(Page.objects.get(pk=2))
        self.assertIsNotNone(page.url)
        self.assertTrue(any(
            'View live' in message.message and page.url in message.message
            for message in response.context['messages']))

    def test_approve_inaccessible(self):
        """
        Edit a page outside of the site root, check the flash message does
        not have a "View live" button.
        """
        response, page = self._approve_page(Page.objects.get(pk=1))
        self.assertIsNone(page.url)
        self.assertFalse(any(
            'View live' in message.message
            for message in response.context['messages']))


class TestParentalM2M(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.events_index = Page.objects.get(url_path='/home/events/')
        self.christmas_page = Page.objects.get(url_path='/home/events/christmas/')
        self.user = self.login()
        self.holiday_category = EventCategory.objects.create(name='Holiday')
        self.men_with_beards_category = EventCategory.objects.create(name='Men with beards')

    def test_create_and_save(self):
        post_data = {
            'title': "Presidents' Day",
            'date_from': "2017-02-20",
            'slug': "presidents-day",
            'audience': "public",
            'location': "America",
            'cost': "$1",
            'carousel_items-TOTAL_FORMS': 0,
            'carousel_items-INITIAL_FORMS': 0,
            'carousel_items-MIN_NUM_FORMS': 0,
            'carousel_items-MAX_NUM_FORMS': 0,
            'speakers-TOTAL_FORMS': 0,
            'speakers-INITIAL_FORMS': 0,
            'speakers-MIN_NUM_FORMS': 0,
            'speakers-MAX_NUM_FORMS': 0,
            'related_links-TOTAL_FORMS': 0,
            'related_links-INITIAL_FORMS': 0,
            'related_links-MIN_NUM_FORMS': 0,
            'related_links-MAX_NUM_FORMS': 0,
            'head_counts-TOTAL_FORMS': 0,
            'head_counts-INITIAL_FORMS': 0,
            'head_counts-MIN_NUM_FORMS': 0,
            'head_counts-MAX_NUM_FORMS': 0,
            'categories': [self.holiday_category.id, self.men_with_beards_category.id]
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:add', args=('tests', 'eventpage', self.events_index.id)),
            post_data
        )
        created_page = EventPage.objects.get(url_path='/home/events/presidents-day/')
        self.assertRedirects(response, reverse('wagtailadmin_pages:edit', args=(created_page.id, )))
        created_revision = created_page.get_latest_revision_as_page()

        self.assertIn(self.holiday_category, created_revision.categories.all())
        self.assertIn(self.men_with_beards_category, created_revision.categories.all())

    def test_create_and_publish(self):
        post_data = {
            'action-publish': "Publish",
            'title': "Presidents' Day",
            'date_from': "2017-02-20",
            'slug': "presidents-day",
            'audience': "public",
            'location': "America",
            'cost': "$1",
            'carousel_items-TOTAL_FORMS': 0,
            'carousel_items-INITIAL_FORMS': 0,
            'carousel_items-MIN_NUM_FORMS': 0,
            'carousel_items-MAX_NUM_FORMS': 0,
            'speakers-TOTAL_FORMS': 0,
            'speakers-INITIAL_FORMS': 0,
            'speakers-MIN_NUM_FORMS': 0,
            'speakers-MAX_NUM_FORMS': 0,
            'related_links-TOTAL_FORMS': 0,
            'related_links-INITIAL_FORMS': 0,
            'related_links-MIN_NUM_FORMS': 0,
            'related_links-MAX_NUM_FORMS': 0,
            'head_counts-TOTAL_FORMS': 0,
            'head_counts-INITIAL_FORMS': 0,
            'head_counts-MIN_NUM_FORMS': 0,
            'head_counts-MAX_NUM_FORMS': 0,
            'categories': [self.holiday_category.id, self.men_with_beards_category.id]
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:add', args=('tests', 'eventpage', self.events_index.id)),
            post_data
        )
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.events_index.id, )))

        created_page = EventPage.objects.get(url_path='/home/events/presidents-day/')
        self.assertIn(self.holiday_category, created_page.categories.all())
        self.assertIn(self.men_with_beards_category, created_page.categories.all())

    def test_edit_and_save(self):
        post_data = {
            'title': "Christmas",
            'date_from': "2017-12-25",
            'slug': "christmas",
            'audience': "public",
            'location': "The North Pole",
            'cost': "Free",
            'carousel_items-TOTAL_FORMS': 0,
            'carousel_items-INITIAL_FORMS': 0,
            'carousel_items-MIN_NUM_FORMS': 0,
            'carousel_items-MAX_NUM_FORMS': 0,
            'speakers-TOTAL_FORMS': 0,
            'speakers-INITIAL_FORMS': 0,
            'speakers-MIN_NUM_FORMS': 0,
            'speakers-MAX_NUM_FORMS': 0,
            'related_links-TOTAL_FORMS': 0,
            'related_links-INITIAL_FORMS': 0,
            'related_links-MIN_NUM_FORMS': 0,
            'related_links-MAX_NUM_FORMS': 0,
            'head_counts-TOTAL_FORMS': 0,
            'head_counts-INITIAL_FORMS': 0,
            'head_counts-MIN_NUM_FORMS': 0,
            'head_counts-MAX_NUM_FORMS': 0,
            'categories': [self.holiday_category.id, self.men_with_beards_category.id]
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:edit', args=(self.christmas_page.id, )),
            post_data
        )
        self.assertRedirects(response, reverse('wagtailadmin_pages:edit', args=(self.christmas_page.id, )))
        updated_page = EventPage.objects.get(id=self.christmas_page.id)
        created_revision = updated_page.get_latest_revision_as_page()

        self.assertIn(self.holiday_category, created_revision.categories.all())
        self.assertIn(self.men_with_beards_category, created_revision.categories.all())

        # no change to live page record yet
        self.assertEqual(0, updated_page.categories.count())

    def test_edit_and_publish(self):
        post_data = {
            'action-publish': "Publish",
            'title': "Christmas",
            'date_from': "2017-12-25",
            'slug': "christmas",
            'audience': "public",
            'location': "The North Pole",
            'cost': "Free",
            'carousel_items-TOTAL_FORMS': 0,
            'carousel_items-INITIAL_FORMS': 0,
            'carousel_items-MIN_NUM_FORMS': 0,
            'carousel_items-MAX_NUM_FORMS': 0,
            'speakers-TOTAL_FORMS': 0,
            'speakers-INITIAL_FORMS': 0,
            'speakers-MIN_NUM_FORMS': 0,
            'speakers-MAX_NUM_FORMS': 0,
            'related_links-TOTAL_FORMS': 0,
            'related_links-INITIAL_FORMS': 0,
            'related_links-MIN_NUM_FORMS': 0,
            'related_links-MAX_NUM_FORMS': 0,
            'head_counts-TOTAL_FORMS': 0,
            'head_counts-INITIAL_FORMS': 0,
            'head_counts-MIN_NUM_FORMS': 0,
            'head_counts-MAX_NUM_FORMS': 0,
            'categories': [self.holiday_category.id, self.men_with_beards_category.id]
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:edit', args=(self.christmas_page.id, )),
            post_data
        )
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.events_index.id, )))
        updated_page = EventPage.objects.get(id=self.christmas_page.id)
        self.assertEqual(2, updated_page.categories.count())
        self.assertIn(self.holiday_category, updated_page.categories.all())
        self.assertIn(self.men_with_beards_category, updated_page.categories.all())


class TestValidationErrorMessages(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.events_index = Page.objects.get(url_path='/home/events/')
        self.christmas_page = Page.objects.get(url_path='/home/events/christmas/')
        self.user = self.login()

    def test_field_error(self):
        """Field errors should be shown against the relevant fields, not in the header message"""
        post_data = {
            'title': "",
            'date_from': "2017-12-25",
            'slug': "christmas",
            'audience': "public",
            'location': "The North Pole",
            'cost': "Free",
            'carousel_items-TOTAL_FORMS': 0,
            'carousel_items-INITIAL_FORMS': 0,
            'carousel_items-MIN_NUM_FORMS': 0,
            'carousel_items-MAX_NUM_FORMS': 0,
            'speakers-TOTAL_FORMS': 0,
            'speakers-INITIAL_FORMS': 0,
            'speakers-MIN_NUM_FORMS': 0,
            'speakers-MAX_NUM_FORMS': 0,
            'related_links-TOTAL_FORMS': 0,
            'related_links-INITIAL_FORMS': 0,
            'related_links-MIN_NUM_FORMS': 0,
            'related_links-MAX_NUM_FORMS': 0,
            'head_counts-TOTAL_FORMS': 0,
            'head_counts-INITIAL_FORMS': 0,
            'head_counts-MIN_NUM_FORMS': 0,
            'head_counts-MAX_NUM_FORMS': 0,
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:edit', args=(self.christmas_page.id, )),
            post_data
        )
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "The page could not be saved due to validation errors")
        # the error should only appear once: against the field, not in the header message
        self.assertContains(response, """<p class="error-message"><span>This field is required.</span></p>""", count=1, html=True)
        self.assertContains(response, "This field is required", count=1)

    def test_non_field_error(self):
        """Non-field errors should be shown in the header message"""
        post_data = {
            'title': "Christmas",
            'date_from': "2017-12-25",
            'date_to': "2017-12-24",
            'slug': "christmas",
            'audience': "public",
            'location': "The North Pole",
            'cost': "Free",
            'carousel_items-TOTAL_FORMS': 0,
            'carousel_items-INITIAL_FORMS': 0,
            'carousel_items-MIN_NUM_FORMS': 0,
            'carousel_items-MAX_NUM_FORMS': 0,
            'speakers-TOTAL_FORMS': 0,
            'speakers-INITIAL_FORMS': 0,
            'speakers-MIN_NUM_FORMS': 0,
            'speakers-MAX_NUM_FORMS': 0,
            'related_links-TOTAL_FORMS': 0,
            'related_links-INITIAL_FORMS': 0,
            'related_links-MIN_NUM_FORMS': 0,
            'related_links-MAX_NUM_FORMS': 0,
            'head_counts-TOTAL_FORMS': 0,
            'head_counts-INITIAL_FORMS': 0,
            'head_counts-MIN_NUM_FORMS': 0,
            'head_counts-MAX_NUM_FORMS': 0,
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:edit', args=(self.christmas_page.id, )),
            post_data
        )
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "The page could not be saved due to validation errors")
        self.assertContains(response, "<li>The end date must be after the start date</li>", count=1)

    def test_field_and_non_field_error(self):
        """
        If both field and non-field errors exist, all errors should be shown in the header message
        with appropriate context to identify the field; and field errors should also be shown
        against the relevant fields.
        """
        post_data = {
            'title': "",
            'date_from': "2017-12-25",
            'date_to': "2017-12-24",
            'slug': "christmas",
            'audience': "public",
            'location': "The North Pole",
            'cost': "Free",
            'carousel_items-TOTAL_FORMS': 0,
            'carousel_items-INITIAL_FORMS': 0,
            'carousel_items-MIN_NUM_FORMS': 0,
            'carousel_items-MAX_NUM_FORMS': 0,
            'speakers-TOTAL_FORMS': 0,
            'speakers-INITIAL_FORMS': 0,
            'speakers-MIN_NUM_FORMS': 0,
            'speakers-MAX_NUM_FORMS': 0,
            'related_links-TOTAL_FORMS': 0,
            'related_links-INITIAL_FORMS': 0,
            'related_links-MIN_NUM_FORMS': 0,
            'related_links-MAX_NUM_FORMS': 0,
            'head_counts-TOTAL_FORMS': 0,
            'head_counts-INITIAL_FORMS': 0,
            'head_counts-MIN_NUM_FORMS': 0,
            'head_counts-MAX_NUM_FORMS': 0,
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:edit', args=(self.christmas_page.id, )),
            post_data
        )
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "The page could not be saved due to validation errors")
        self.assertContains(response, "<li>The end date must be after the start date</li>", count=1)

        # Error on title shown against the title field
        self.assertContains(response, """<p class="error-message"><span>This field is required.</span></p>""", count=1, html=True)
        # Error on title shown in the header message
        self.assertContains(response, "<li>Title: This field is required.</li>", count=1)


class TestNestedInlinePanel(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.events_index = Page.objects.get(url_path='/home/events/')
        self.christmas_page = EventPage.objects.get(url_path='/home/events/christmas/')
        self.speaker = self.christmas_page.speakers.first()
        self.speaker.awards.create(
            name="Beard Of The Year", date_awarded=datetime.date(1997, 12, 25)
        )
        self.speaker.save()
        self.user = self.login()

    def test_get_edit_form(self):
        response = self.client.get(
            reverse('wagtailadmin_pages:edit', args=(self.christmas_page.id, ))
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            """<input type="text" name="speakers-0-awards-0-name" value="Beard Of The Year" maxlength="255" id="id_speakers-0-awards-0-name">""",
            count=1, html=True
        )

        # there should be no "extra" forms, as the nested formset should respect the extra_form_count=0 set on WagtailAdminModelForm
        self.assertContains(
            response,
            """<input type="hidden" name="speakers-0-awards-TOTAL_FORMS" value="1" id="id_speakers-0-awards-TOTAL_FORMS">""",
            count=1, html=True
        )
        self.assertContains(
            response,
            """<input type="text" name="speakers-0-awards-1-name" value="" maxlength="255" id="id_speakers-0-awards-1-name">""",
            count=0, html=True
        )

        # date field should use AdminDatePicker
        self.assertContains(
            response,
            """<input type="text" name="speakers-0-awards-0-date_awarded" value="1997-12-25" autocomplete="off" id="id_speakers-0-awards-0-date_awarded">""",
            count=1, html=True
        )

    def test_post_edit(self):
        post_data = nested_form_data({
            'title': "Christmas",
            'date_from': "2017-12-25",
            'date_to': "2017-12-25",
            'slug': "christmas",
            'audience': "public",
            'location': "The North Pole",
            'cost': "Free",
            'carousel_items': inline_formset([]),
            'speakers': inline_formset([
                {
                    'id': self.speaker.id,
                    'first_name': "Jeff",
                    'last_name': "Christmas",
                    'awards': inline_formset([
                        {
                            'id': self.speaker.awards.first().id,
                            'name': "Beard Of The Century",
                            'date_awarded': "1997-12-25",
                        },
                        {
                            'name': "Bobsleigh Olympic gold medallist",
                            'date_awarded': "2018-02-01",
                        },
                    ], initial=1)
                },
            ], initial=1),
            'related_links': inline_formset([]),
            'head_counts': inline_formset([]),
            'action-publish': "Publish",
        })
        response = self.client.post(
            reverse('wagtailadmin_pages:edit', args=(self.christmas_page.id, )),
            post_data
        )
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.events_index.id, )))

        new_christmas_page = EventPage.objects.get(url_path='/home/events/christmas/')
        self.assertEqual(new_christmas_page.speakers.first().first_name, "Jeff")
        awards = new_christmas_page.speakers.first().awards.all()
        self.assertEqual(len(awards), 2)
        self.assertEqual(awards[0].name, "Beard Of The Century")
        self.assertEqual(awards[1].name, "Bobsleigh Olympic gold medallist")


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestLocaleSelector(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.christmas_page = EventPage.objects.get(url_path='/home/events/christmas/')
        self.fr_locale = Locale.objects.create(language_code='fr')
        self.translated_christmas_page = self.christmas_page.copy_for_translation(self.fr_locale, copy_parents=True)
        self.user = self.login()

    def test_locale_selector(self):
        response = self.client.get(
            reverse('wagtailadmin_pages:edit', args=[self.christmas_page.id])
        )

        self.assertContains(response, '<li class="header-meta--locale">')

        edit_translation_url = reverse('wagtailadmin_pages:edit', args=[self.translated_christmas_page.id])
        self.assertContains(response, f'<a href="{edit_translation_url}" aria-label="French" class="u-link is-live">')

    @override_settings(WAGTAIL_I18N_ENABLED=False)
    def test_locale_selector_not_present_when_i18n_disabled(self):
        response = self.client.get(
            reverse('wagtailadmin_pages:edit', args=[self.christmas_page.id])
        )

        self.assertNotContains(response, '<li class="header-meta--locale">')

        edit_translation_url = reverse('wagtailadmin_pages:edit', args=[self.translated_christmas_page.id])
        self.assertNotContains(response, f'<a href="{edit_translation_url}" aria-label="French" class="u-link is-live">')

    def test_locale_dropdown_not_present_without_permission_to_edit(self):
        # Remove user's permissions to edit French tree
        en_events_index = Page.objects.get(url_path='/home/events/')
        group = Group.objects.get(name='Moderators')
        GroupPagePermission.objects.create(
            group=group,
            page=en_events_index,
            permission_type='edit',
        )
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.groups.add(group)
        self.user.save()

        # Locale indicator should exist, but the "French" option should be hidden
        response = self.client.get(
            reverse('wagtailadmin_pages:edit', args=[self.christmas_page.id])
        )

        self.assertContains(response, '<li class="header-meta--locale">')

        edit_translation_url = reverse('wagtailadmin_pages:edit', args=[self.translated_christmas_page.id])
        self.assertNotContains(response, f'<a href="{edit_translation_url}" aria-label="French" class="u-link is-live">')
