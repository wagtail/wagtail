from django.contrib.auth import get_user_model
from django.test import TestCase

from wagtail.models import Comment, Page, CommentReply, PageSubscription
from django.core import mail


class CommentTestingUtils:
    def setUp(self):
        self.page = Page.objects.get(title="Welcome to the Wagtail test site!")
        self.revision_1 = self.page.save_revision()
        self.revision_2 = self.page.save_revision()

    def create_comment(self, revision_created):
        return Comment.objects.create(
            page=self.page,
            user=get_user_model().objects.first(),
            text="test",
            contentpath="title",
            revision_created=revision_created,
        )


class TestRevisionDeletion(CommentTestingUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        super().setUp()
        self.revision_3 = self.page.save_revision()
        self.old_comment = self.create_comment(self.revision_1)
        self.new_comment = self.create_comment(self.revision_3)

    def test_deleting_old_revision_moves_comment_revision_created_forwards(self):
        # test that when a revision is deleted, a comment linked to it via revision_created has its revision_created moved
        # to the next revision
        self.revision_1.delete()
        self.old_comment.refresh_from_db()
        self.assertEqual(self.old_comment.revision_created, self.revision_2)

    def test_deleting_most_recent_revision_deletes_created_comments(self):
        # test that when the most recent revision is deleted, any comments created on it are also deleted
        self.revision_3.delete()
        with self.assertRaises(Comment.DoesNotExist):
            self.new_comment.refresh_from_db()


class TestEmailNotification(TestCase):
    def setUp(self):
        self.page = Page.objects.get(id=2)
        self.revision_1 = self.page.save_revision()
        self.revision_2 = self.page.save_revision()

        # Create users for testing
        self.moderator_user = get_user_model().objects.create(
            username="moderator", email="moderator@example.com"
        )
        self.reply_user = get_user_model().objects.create(
            username="replyuser12", email="replyuser12@example.com"
        )

    def create_comment(self, revision_created, user=None, parent_comment=None):
        if user is None:
            user = get_user_model().objects.create(
                username="username", email="user@example.com"
            )
        comment = Comment.objects.create(
            page=self.page,
            user=user,
            text="test",
            contentpath="title",
            revision_created=revision_created,
        )
        if parent_comment:
            reply_user = self.reply_user
            reply = CommentReply.objects.create(
                comment=parent_comment,
                user=reply_user,
                text="reply text",
            )
            page_subscription, created = PageSubscription.objects.get_or_create(
                user=parent_comment.user,
                page=parent_comment.page,
                comment_notifications=True,
            )
        return comment

    def test_comment_creation_with_reply(self):
        revision = self.page.get_latest_revision()

        # Create the main comment with the main user
        comment = self.create_comment(revision, self.moderator_user)
        self.assertIsNotNone(comment, "Comment not created successfully")
        self.assertEqual(
            Comment.objects.count(), 1
        )  # Check if the comment is created in the database

        # Add a reply to the previous comment with a different user
        reply_comment = self.create_comment(
            revision, self.reply_user, parent_comment=comment
        )
        self.assertIsNotNone(reply_comment, "Reply not created successfully")
        self.assertEqual(
            CommentReply.objects.count(), 1
        )  # Check if the reply is created in the database
