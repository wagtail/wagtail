from django.contrib.auth import get_user_model
from django.test import TestCase

from wagtail.models import Comment, Page
from wagtail.test.testapp.models import CommentableJSONPage
from wagtail.test.utils import WagtailTestUtils


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


class TestContentPath(WagtailTestUtils, TestCase):
    def setUp(self):
        self.root_page = Page.get_first_root_node()
        self.commentable_page = CommentableJSONPage(
            title="Commentable JSON Page",
            slug="commentable-json-page",
            commentable_body={
                "header": {
                    "title": "Comments are Welcome",
                },
            },
            uncommentable_body={
                "title": "No feedback here",
            },
            stream_body=[
                {
                    "id": "1",
                    "type": "text",
                    "value": "This allows comments",
                }
            ],
        )

        self.root_page.add_child(instance=self.commentable_page)
        self.user = self.create_test_user()

    def test_valid_path_for_streamfield(self):
        comment = Comment.objects.create(
            page=self.commentable_page,
            user=self.user,
            text="test",
            contentpath="stream_body.1",
        )
        self.assertTrue(comment.has_valid_contentpath(self.commentable_page))

    def test_valid_path_for_contentpath_field(self):
        comment = Comment.objects.create(
            page=self.commentable_page,
            user=self.user,
            text="test",
            contentpath="commentable_body.header.title",
        )
        self.assertTrue(comment.has_valid_contentpath(self.commentable_page))

    def test_invalid_path_for_contentpath_field(self):
        comment = Comment.objects.create(
            page=self.commentable_page,
            user=self.user,
            text="test",
            contentpath="commentable_body.header.not_valid",
        )
        self.assertFalse(comment.has_valid_contentpath(self.commentable_page))

    def test_valid_path_for_non_contentpath_field(self):
        comment = Comment.objects.create(
            page=self.commentable_page,
            user=self.user,
            text="test",
            contentpath="uncommentable_body.title",
        )
        self.assertFalse(comment.has_valid_contentpath(self.commentable_page))
