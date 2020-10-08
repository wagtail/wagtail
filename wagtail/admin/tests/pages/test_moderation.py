import logging

from itertools import chain
from unittest import mock

from django.contrib.auth.models import Group, Permission
from django.contrib.messages import constants as message_constants
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail.core.models import Page, PageRevision
from wagtail.core.signals import page_published
from wagtail.tests.testapp.models import SimplePage
from wagtail.tests.utils import WagtailTestUtils
from wagtail.users.models import UserProfile


class TestApproveRejectModeration(TestCase, WagtailTestUtils):
    def setUp(self):
        self.submitter = self.create_superuser(
            username='submitter',
            email='submitter@email.com',
            password='password',
        )

        self.user = self.login()

        # Create a page and submit it for moderation
        root_page = Page.objects.get(id=2)
        self.page = SimplePage(
            title="Hello world!",
            slug='hello-world',
            content="hello",
            live=False,
            has_unpublished_changes=True,
        )
        root_page.add_child(instance=self.page)

        self.page.save_revision(user=self.submitter, submitted_for_moderation=True)
        self.revision = self.page.get_latest_revision()

    def test_approve_moderation_view(self):
        """
        This posts to the approve moderation view and checks that the page was approved
        """
        # Connect a mock signal handler to page_published signal
        mock_handler = mock.MagicMock()
        page_published.connect(mock_handler)

        # Post
        response = self.client.post(reverse('wagtailadmin_pages:approve_moderation', args=(self.revision.id, )))

        # Check that the user was redirected to the dashboard
        self.assertRedirects(response, reverse('wagtailadmin_home'))

        page = Page.objects.get(id=self.page.id)
        # Page must be live
        self.assertTrue(page.live, "Approving moderation failed to set live=True")
        # Page should now have no unpublished changes
        self.assertFalse(
            page.has_unpublished_changes,
            "Approving moderation failed to set has_unpublished_changes=False"
        )

        # Check that the page_published signal was fired
        self.assertEqual(mock_handler.call_count, 1)
        mock_call = mock_handler.mock_calls[0][2]

        self.assertEqual(mock_call['sender'], self.page.specific_class)
        self.assertEqual(mock_call['instance'], self.page)
        self.assertIsInstance(mock_call['instance'], self.page.specific_class)

    def test_approve_moderation_when_later_revision_exists(self):
        self.page.title = "Goodbye world!"
        self.page.save_revision(user=self.submitter, submitted_for_moderation=False)

        response = self.client.post(reverse('wagtailadmin_pages:approve_moderation', args=(self.revision.id, )))

        # Check that the user was redirected to the dashboard
        self.assertRedirects(response, reverse('wagtailadmin_home'))

        page = Page.objects.get(id=self.page.id)
        # Page must be live
        self.assertTrue(page.live, "Approving moderation failed to set live=True")
        # Page content should be the submitted version, not the published one
        self.assertEqual(page.title, "Hello world!")
        # Page should still have unpublished changes
        self.assertTrue(
            page.has_unpublished_changes,
            "has_unpublished_changes incorrectly cleared on approve_moderation when a later revision exists"
        )

    def test_approve_moderation_view_bad_revision_id(self):
        """
        This tests that the approve moderation view handles invalid revision ids correctly
        """
        # Post
        response = self.client.post(reverse('wagtailadmin_pages:approve_moderation', args=(12345, )))

        # Check that the user received a 404 response
        self.assertEqual(response.status_code, 404)

    def test_approve_moderation_view_bad_permissions(self):
        """
        This tests that the approve moderation view doesn't allow users without moderation permissions
        """
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        # Post
        response = self.client.post(reverse('wagtailadmin_pages:approve_moderation', args=(self.revision.id, )))

        # Check that the user received a 302 redirected response
        self.assertEqual(response.status_code, 302)

    def test_reject_moderation_view(self):
        """
        This posts to the reject moderation view and checks that the page was rejected
        """
        # Post
        response = self.client.post(reverse('wagtailadmin_pages:reject_moderation', args=(self.revision.id, )))

        # Check that the user was redirected to the dashboard
        self.assertRedirects(response, reverse('wagtailadmin_home'))

        # Page must not be live
        self.assertFalse(Page.objects.get(id=self.page.id).live)

        # Revision must no longer be submitted for moderation
        self.assertFalse(PageRevision.objects.get(id=self.revision.id).submitted_for_moderation)

    def test_reject_moderation_view_bad_revision_id(self):
        """
        This tests that the reject moderation view handles invalid revision ids correctly
        """
        # Post
        response = self.client.post(reverse('wagtailadmin_pages:reject_moderation', args=(12345, )))

        # Check that the user received a 404 response
        self.assertEqual(response.status_code, 404)

    def test_reject_moderation_view_bad_permissions(self):
        """
        This tests that the reject moderation view doesn't allow users without moderation permissions
        """
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        # Post
        response = self.client.post(reverse('wagtailadmin_pages:reject_moderation', args=(self.revision.id, )))

        # Check that the user received a 302 redirected response
        self.assertEqual(response.status_code, 302)

    def test_preview_for_moderation(self):
        response = self.client.get(reverse('wagtailadmin_pages:preview_for_moderation', args=(self.revision.id, )))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tests/simple_page.html')
        self.assertContains(response, "Hello world!")


class TestNotificationPreferences(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Login
        self.user = self.login()

        # Create two moderator users for testing 'submitted' email
        self.moderator = self.create_superuser('moderator', 'moderator@email.com', 'password')
        self.moderator2 = self.create_superuser('moderator2', 'moderator2@email.com', 'password')

        # Create a submitter for testing 'rejected' and 'approved' emails
        self.submitter = self.create_user('submitter', 'submitter@email.com', 'password')

        # User profiles for moderator2 and the submitter
        self.moderator2_profile = UserProfile.get_for_user(self.moderator2)
        self.submitter_profile = UserProfile.get_for_user(self.submitter)

        # Create a page and submit it for moderation
        self.child_page = SimplePage(
            title="Hello world!",
            slug='hello-world',
            content="hello",
            live=False,
        )
        self.root_page.add_child(instance=self.child_page)

        # POST data to edit the page
        self.post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-submit': "Submit",
        }

    def submit(self):
        return self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), self.post_data)

    def silent_submit(self):
        """
        Sets up the child_page as needing moderation, without making a request
        """
        self.child_page.save_revision(user=self.submitter, submitted_for_moderation=True)
        self.revision = self.child_page.get_latest_revision()

    def approve(self):
        return self.client.post(reverse('wagtailadmin_pages:approve_moderation', args=(self.revision.id, )))

    def reject(self):
        return self.client.post(reverse('wagtailadmin_pages:reject_moderation', args=(self.revision.id, )))

    def test_vanilla_profile(self):
        # Check that the vanilla profile has rejected notifications on
        self.assertEqual(self.submitter_profile.rejected_notifications, True)

        # Check that the vanilla profile has approved notifications on
        self.assertEqual(self.submitter_profile.approved_notifications, True)

    def test_approved_notifications(self):
        # Set up the page version
        self.silent_submit()
        # Approve
        self.approve()

        # Submitter must receive an approved email
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['submitter@email.com'])
        self.assertEqual(mail.outbox[0].subject, 'The page "Hello world!" has been approved')

    def test_approved_notifications_preferences_respected(self):
        # Submitter doesn't want 'approved' emails
        self.submitter_profile.approved_notifications = False
        self.submitter_profile.save()

        # Set up the page version
        self.silent_submit()
        # Approve
        self.approve()

        # No email to send
        self.assertEqual(len(mail.outbox), 0)

    def test_rejected_notifications(self):
        # Set up the page version
        self.silent_submit()
        # Reject
        self.reject()

        # Submitter must receive a rejected email
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['submitter@email.com'])
        self.assertEqual(mail.outbox[0].subject, 'The page "Hello world!" has been rejected')

    def test_rejected_notification_preferences_respected(self):
        # Submitter doesn't want 'rejected' emails
        self.submitter_profile.rejected_notifications = False
        self.submitter_profile.save()

        # Set up the page version
        self.silent_submit()
        # Reject
        self.reject()

        # No email to send
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(WAGTAILADMIN_NOTIFICATION_INCLUDE_SUPERUSERS=False)
    def test_disable_superuser_notification(self):
        # Add one of the superusers to the moderator group
        self.moderator.groups.add(Group.objects.get(name='Moderators'))

        response = self.submit()

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        # Check that the non-moderator superuser is not being notified
        expected_emails = 1
        self.assertEqual(len(mail.outbox), expected_emails)
        # Use chain as the 'to' field is a list of recipients
        email_to = list(chain.from_iterable([m.to for m in mail.outbox]))
        self.assertIn(self.moderator.email, email_to)
        self.assertNotIn(self.moderator2.email, email_to)

    @mock.patch.object(EmailMultiAlternatives, 'send', side_effect=IOError('Server down'))
    def test_email_send_error(self, mock_fn):
        logging.disable(logging.CRITICAL)
        # Approve
        self.silent_submit()
        response = self.approve()
        logging.disable(logging.NOTSET)

        # An email that fails to send should return a message rather than crash the page
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse('wagtailadmin_home'))

        # There should be one "approved" message and one "failed to send notifications"
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].level, message_constants.SUCCESS)
        self.assertEqual(messages[1].level, message_constants.ERROR)

    def test_email_headers(self):
        # Submit
        self.submit()

        msg_headers = set(mail.outbox[0].message().items())
        headers = {('Auto-Submitted', 'auto-generated')}
        self.assertTrue(headers.issubset(msg_headers), msg='Message is missing the Auto-Submitted header.',)
