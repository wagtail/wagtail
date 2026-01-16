from unittest import mock

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from wagtail.models import (
    Comment,
    Page,
    PageSubscription,
)
from wagtail.test.testapp.models import SimplePage
from wagtail.test.utils import WagtailTestUtils


class TestCommentNotifications(WagtailTestUtils, TestCase):
    def setUp(self):
        self.root_page = Page.objects.get(id=2)
        self.child_page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            content="hello",
        )
        self.root_page.add_child(instance=self.child_page)
        self.child_page.save_revision().publish()

        self.user = self.login()

    def test_comment_only_action_triggers_notification(self):
        subscriber = self.create_user("subscriber")
        PageSubscription.objects.create(
            page=self.child_page, user=subscriber, comment_notifications=True
        )

        comment = Comment.objects.create(
            page=self.child_page,
            user=self.user,
            text="Initial comment",
            contentpath="title",
        )

        post_data = {
            "title": "Hello world!",
            "content": "hello",
            "slug": "hello-world",
            "comments-TOTAL_FORMS": "1",
            "comments-INITIAL_FORMS": "1",
            "comments-MIN_NUM_FORMS": "0",
            "comments-0-resolved": "on",
            "comments-0-id": str(comment.id),
            "comments-0-contentpath": "title",
            "comments-0-text": "Initial comment",
            "comments-0-replies-TOTAL_FORMS": "0",
            "comments-0-replies-INITIAL_FORMS": "0",
        }

        mail.outbox = []
        self.client.post(
            reverse("wagtailadmin_pages:edit", args=[self.child_page.id]), post_data
        )

        self.assertEqual(
            len(mail.outbox), 1, "Notification was not sent for comment-only action"
        )

    def test_scoping_bug_fixed(self):
        user_a = self.create_user("user_a")
        user_b = self.create_user("user_b")

        # User A is subscribed to thread 1
        comment_1 = Comment.objects.create(
            page=self.child_page, user=user_a, text="Thread 1", contentpath="title"
        )
        # User B is subscribed to thread 2
        comment_2 = Comment.objects.create(
            page=self.child_page, user=user_b, text="Thread 2", contentpath="title"
        )

        post_data = {
            "title": "Hello world!",
            "content": "hello",
            "slug": "hello-world",
            "comments-TOTAL_FORMS": "2",
            "comments-INITIAL_FORMS": "2",
            "comments-0-id": str(comment_1.id),
            "comments-0-text": "Thread 1",
            "comments-0-contentpath": "title",
            "comments-0-replies-TOTAL_FORMS": "1",
            "comments-0-replies-INITIAL_FORMS": "0",
            "comments-0-replies-0-text": "Reply to 1",
            "comments-1-id": str(comment_2.id),
            "comments-1-text": "Thread 2",
            "comments-1-contentpath": "title",
            "comments-1-replies-TOTAL_FORMS": "1",
            "comments-1-replies-INITIAL_FORMS": "0",
            "comments-1-replies-0-text": "Reply to 2",
        }

        mail.outbox = []
        self.client.post(
            reverse("wagtailadmin_pages:edit", args=[self.child_page.id]), post_data
        )

        self.assertEqual(len(mail.outbox), 2)

        email_a = next(e for e in mail.outbox if user_a.email in e.to)
        email_b = next(e for e in mail.outbox if user_b.email in e.to)

        self.assertIn("Reply to 1", email_a.body)
        self.assertNotIn("Reply to 2", email_a.body)
        self.assertIn("Reply to 2", email_b.body)
        self.assertNotIn("Reply to 1", email_b.body)

    @mock.patch("wagtail.admin.mail.get_connection")
    def test_no_500_error_on_notification_failure(self, mock_get_connection):
        mock_get_connection.side_effect = Exception("SMTP error")
        subscriber = self.create_user("subscriber")
        PageSubscription.objects.create(
            page=self.child_page, user=subscriber, comment_notifications=True
        )

        post_data = {
            "title": "Hello world!",
            "content": "hello",
            "slug": "hello-world",
            "comments-TOTAL_FORMS": "1",
            "comments-INITIAL_FORMS": "0",
            "comments-0-text": "A test comment",
            "comments-0-contentpath": "title",
            "comments-0-replies-TOTAL_FORMS": "0",
            "comments-0-replies-INITIAL_FORMS": "0",
        }

        response = self.client.post(
            reverse("wagtailadmin_pages:edit", args=[self.child_page.id]), post_data
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Comment.objects.filter(text="A test comment").exists())
