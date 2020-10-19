from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from wagtail.core.models import Comment, Page


class CommentTestingUtils:
    def setUp(self):
        self.page = Page.objects.get(title="Welcome to the Wagtail test site!")
        self.revision_1 = self.page.save_revision()
        self.revision_2 = self.page.save_revision()

    def create_comment(self, revision_created, revision_resolved=None):
        return Comment.objects.create(
            page=self.page,
            user=get_user_model().objects.first(),
            text='test',
            contentpath='title',
            revision_created=revision_created,
            revision_resolved=revision_resolved
        )


class TestCommentModels(CommentTestingUtils, TestCase):
    fixtures = ['test.json']

    def test_revision_resolved_not_after_revision_created_raises_error(self):
        with self.assertRaises(ValidationError):
            self.create_comment(self.revision_2, revision_resolved=self.revision_1)

        with self.assertRaises(ValidationError):
            self.create_comment(self.revision_1, revision_resolved=self.revision_1)


class TestRevisionDeletion(CommentTestingUtils, TestCase):
    fixtures = ['test.json']

    def setUp(self):
        super().setUp()
        self.revision_3 = self.page.save_revision()
        self.old_comment = self.create_comment(self.revision_1)
        self.old_resolved_comment = self.create_comment(self.revision_1, revision_resolved=self.revision_2)
        self.newly_resolved_comment = self.create_comment(self.revision_1, revision_resolved=self.revision_3)
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

    def test_revision_deletion_when_revision_resolved_is_next_revision(self):
        # test that when a comment's revision_created and revision_resolved are neighbouring revisions, deleting the revision_created
        # deletes the comment, as a comment's revision_resolved must be after its revision_created
        self.revision_1.delete()
        with self.assertRaises(Comment.DoesNotExist):
            self.old_resolved_comment.refresh_from_db()

    def test_deleting_resolving_revision(self):
        # test that when a revision linked to a comment via its revision_resolved is deleted, the comment's revision_resolved is
        # moved to the next revision, or unresolved if there is none
        self.revision_2.delete()
        self.old_resolved_comment.refresh_from_db()
        self.assertEqual(self.old_resolved_comment.revision_resolved, self.revision_3)

        self.revision_3.delete()
        self.newly_resolved_comment.refresh_from_db()
        self.assertIsNone(self.newly_resolved_comment.revision_resolved)
