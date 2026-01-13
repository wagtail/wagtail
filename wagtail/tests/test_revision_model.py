import datetime

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from freezegun import freeze_time

from wagtail.models import Page, Revision, get_default_page_content_type
from wagtail.test.testapp.models import (
    FullFeaturedSnippet,
    RevisableChildModel,
    RevisableGrandChildModel,
    RevisableModel,
    SimplePage,
)
from wagtail.test.utils import WagtailTestUtils


class TestRevisableModel(WagtailTestUtils, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.instance = RevisableModel.objects.create(text="foo")
        cls.content_type = ContentType.objects.get_for_model(RevisableModel)

    @classmethod
    def create_page(cls):
        homepage = Page.objects.get(url_path="/home/")
        hello_page = SimplePage(
            title="Hello world", slug="hello-world", content="hello"
        )
        homepage.add_child(instance=hello_page)
        return hello_page

    def test_can_save_revision(self):
        self.instance.text = "updated"
        revision = self.instance.save_revision()
        revision_from_db = self.instance.revisions.first()
        self.instance.refresh_from_db()

        self.assertEqual(revision, revision_from_db)
        # The latest revision should be set
        self.assertEqual(self.instance.latest_revision, revision_from_db)
        # The revision should have the updated data
        self.assertEqual(revision_from_db.content["text"], "updated")
        # Only saving a revision should not update the instance itself
        self.assertEqual(self.instance.text, "foo")

    def test_get_latest_revision_exists(self):
        self.instance.text = "updated"
        self.instance.save_revision()
        self.instance.text = "updated twice"
        revision = self.instance.save_revision()
        self.instance.refresh_from_db()

        with self.assertNumQueries(1):
            # Should be able to query directly using latest_revision ForeignKey
            revision_from_db = self.instance.get_latest_revision()

        self.assertEqual(revision, revision_from_db)
        self.assertEqual(revision_from_db.content["text"], "updated twice")

    def test_content_type_without_inheritance(self):
        self.instance.text = "updated"
        revision = self.instance.save_revision()

        revision_from_db = Revision.objects.filter(
            base_content_type=self.content_type,
            content_type=self.content_type,
            object_id=self.instance.pk,
        ).first()

        self.assertEqual(revision, revision_from_db)
        self.assertEqual(self.instance.get_base_content_type(), self.content_type)
        self.assertEqual(self.instance.get_content_type(), self.content_type)

        # The for_instance() method should return the revision
        self.assertEqual(Revision.objects.for_instance(self.instance).first(), revision)

    def test_content_type_with_inheritance(self):
        instance = RevisableGrandChildModel.objects.create(text="test")
        instance.text = "test updated"
        revision = instance.save_revision()

        base_content_type = self.content_type
        content_type = ContentType.objects.get_for_model(RevisableGrandChildModel)
        revision_from_db = Revision.objects.filter(
            base_content_type=base_content_type,
            content_type=content_type,
            object_id=instance.pk,
        ).first()

        self.assertEqual(revision, revision_from_db)
        self.assertEqual(instance.get_base_content_type(), base_content_type)
        self.assertEqual(instance.get_content_type(), content_type)

        # The `for_instance()` method of `Revision.objects` and the model's
        # `revisions` property should return the revision,
        # whether we're using the most specific instance
        self.assertIsInstance(instance, RevisableModel)
        self.assertIsInstance(instance, RevisableChildModel)
        self.assertIsInstance(instance, RevisableGrandChildModel)
        self.assertEqual(Revision.objects.for_instance(instance).first(), revision)
        self.assertEqual(instance.revisions.first(), revision)

        # the intermediary instance
        intermediary_instance = RevisableChildModel.objects.get(pk=instance.pk)
        self.assertIsInstance(intermediary_instance, RevisableModel)
        self.assertIsInstance(intermediary_instance, RevisableChildModel)
        self.assertNotIsInstance(intermediary_instance, RevisableGrandChildModel)
        self.assertEqual(
            Revision.objects.for_instance(intermediary_instance).first(),
            revision,
        )
        self.assertEqual(intermediary_instance.revisions.first(), revision)

        # or the base instance
        base_instance = RevisableModel.objects.get(pk=instance.pk)
        self.assertIsInstance(base_instance, RevisableModel)
        self.assertNotIsInstance(base_instance, RevisableGrandChildModel)
        self.assertEqual(Revision.objects.for_instance(base_instance).first(), revision)
        self.assertEqual(base_instance.revisions.first(), revision)

    def test_content_type_for_page_model(self):
        hello_page = self.create_page()
        hello_page.content = "Updated world"
        revision = hello_page.save_revision()

        base_content_type = get_default_page_content_type()
        content_type = ContentType.objects.get_for_model(SimplePage)
        revision_from_db = Revision.objects.filter(
            base_content_type=base_content_type,
            content_type=content_type,
            object_id=hello_page.pk,
        ).first()

        self.assertEqual(revision, revision_from_db)
        self.assertEqual(hello_page.get_base_content_type(), base_content_type)
        self.assertEqual(hello_page.get_content_type(), content_type)

        # The `for_instance()` method of `Revision.objects` and the model's
        # `revisions` property should return the revision,
        # whether we're using the specific instance
        self.assertIsInstance(hello_page, SimplePage)
        self.assertIsInstance(hello_page, Page)
        self.assertEqual(Revision.objects.for_instance(hello_page).first(), revision)
        self.assertEqual(hello_page.revisions.first(), revision)

        # or the base instance
        base_instance = Page.objects.get(pk=hello_page.pk)
        self.assertIsInstance(base_instance, Page)
        self.assertNotIsInstance(base_instance, SimplePage)
        self.assertEqual(Revision.objects.for_instance(base_instance).first(), revision)
        self.assertEqual(base_instance.revisions.first(), revision)

    def test_as_object(self):
        self.instance.text = "updated"
        self.instance.save_revision()
        self.instance.refresh_from_db()
        revision = self.instance.revisions.first()
        instance = revision.as_object()

        self.assertIsInstance(instance, RevisableModel)
        # The instance created from the revision should be updated
        self.assertEqual(instance.text, "updated")
        # Only saving a revision should not update the instance itself
        self.assertEqual(self.instance.text, "foo")

    def test_as_object_with_page(self):
        hello_page = self.create_page()
        hello_page.content = "updated"
        hello_page.save_revision()
        hello_page.refresh_from_db()
        revision = hello_page.revisions.first()
        instance = revision.as_object()

        # The instance should be of the specific page class.
        self.assertIsInstance(instance, SimplePage)
        self.assertEqual(instance.content, "updated")
        self.assertEqual(hello_page.content, "hello")

    def test_is_latest_revision_newer_creation_date_and_id(self):
        first = self.instance.save_revision()
        self.assertTrue(first.is_latest_revision())

        second = self.instance.save_revision()
        self.assertFalse(first.is_latest_revision())
        self.assertTrue(second.is_latest_revision())

        # Normal case, both creation date and id are newer
        self.assertLess(first.created_at, second.created_at)
        self.assertLess(first.id, second.id)

    def test_is_latest_revision_newer_creation_date_older_id(self):
        first = self.instance.save_revision()
        self.assertTrue(first.is_latest_revision())

        second = self.instance.save_revision()
        first.created_at = second.created_at + datetime.timedelta(days=9)
        first.save()

        self.assertTrue(first.is_latest_revision())
        self.assertFalse(second.is_latest_revision())

        # The creation date takes precedence over the id
        self.assertGreater(first.created_at, second.created_at)
        self.assertLess(first.id, second.id)

    @freeze_time("2023-01-19")
    def test_is_latest_revision_same_creation_dates(self):
        first = self.instance.save_revision()
        self.assertTrue(first.is_latest_revision())

        second = self.instance.save_revision()
        self.assertFalse(first.is_latest_revision())
        self.assertTrue(second.is_latest_revision())

        # The id is used as a tie breaker
        self.assertEqual(first.created_at, second.created_at)
        self.assertLess(first.id, second.id)

    def test_revision_cascade_on_object_delete(self):
        page = self.create_page()
        full_featured_snippet = FullFeaturedSnippet.objects.create(text="foo")
        # The RevisionMixin should provide a default `GenericRelation` so that
        # revisions are deleted when the object is deleted, even if the
        # model does not explicitly define a `GenericRelation` to `Revision`.
        cases = [
            page,
            full_featured_snippet,
            self.instance,  # No explicit GenericRelation to Revision
        ]
        for instance in cases:
            with self.subTest(instance=instance):
                revision = instance.save_revision()
                query = {
                    "base_content_type": instance.get_base_content_type(),
                    "object_id": str(instance.pk),
                }
                self.assertEqual(Revision.objects.filter(**query).first(), revision)
                instance.delete()
                self.assertIs(Revision.objects.filter(**query).exists(), False)

    def test_overwrite_revision(self):
        self.instance.text = "Existing revision"
        revision1 = self.instance.save_revision()
        self.assertEqual(self.instance.revisions.count(), 1)
        self.instance.text = "Updated revision"
        revision2 = self.instance.save_revision(overwrite_revision=revision1)
        self.assertEqual(self.instance.revisions.count(), 1)
        self.assertEqual(revision1.id, revision2.id)
        revision1.refresh_from_db()
        self.assertEqual(revision1.content["text"], "Updated revision")

    def test_cannot_overwrite_revision_that_is_not_latest(self):
        self.instance.text = "Existing revision"
        revision1 = self.instance.save_revision()
        self.assertEqual(self.instance.revisions.count(), 1)
        self.instance.text = "Second revision"
        self.instance.save_revision()
        self.assertEqual(self.instance.revisions.count(), 2)
        self.instance.text = "Updated revision"
        with self.assertRaisesMessage(
            PermissionDenied,
            "Cannot overwrite a revision that is not the latest for this "
            "revisable model.",
        ):
            self.instance.save_revision(overwrite_revision=revision1)

        self.assertEqual(self.instance.revisions.count(), 2)
        latest_revision = self.instance.get_latest_revision()
        self.assertEqual(latest_revision.content["text"], "Second revision")

    def test_cannot_overwrite_revision_from_other_instance(self):
        self.instance.text = "Existing revision"
        self.instance.save_revision()

        other_instance = RevisableModel.objects.create(text="other")
        other_instance.text = "Existing other revision"
        revision1 = other_instance.save_revision()

        self.instance.text = "Updated revision"
        with self.assertRaisesMessage(
            PermissionDenied,
            "Cannot overwrite a revision that is not the latest for this "
            "revisable model.",
        ):
            self.instance.save_revision(overwrite_revision=revision1)

        self.assertEqual(self.instance.revisions.count(), 1)
        latest_revision = self.instance.get_latest_revision()
        self.assertEqual(latest_revision.content["text"], "Existing revision")

        self.assertEqual(other_instance.revisions.count(), 1)
        latest_revision = other_instance.get_latest_revision()
        self.assertEqual(latest_revision.content["text"], "Existing other revision")

    def test_overwrite_revision_with_user_id(self):
        user = self.create_user("user1")
        self.instance.text = "Existing revision"
        revision1 = self.instance.save_revision(user=user)
        self.assertEqual(self.instance.revisions.count(), 1)
        self.instance.text = "Updated revision"
        revision2 = self.instance.save_revision(overwrite_revision=revision1, user=user)
        self.assertEqual(self.instance.revisions.count(), 1)
        self.assertEqual(revision1.id, revision2.id)
        revision1.refresh_from_db()
        self.assertEqual(revision1.content["text"], "Updated revision")

    def test_cannot_overwrite_revision_with_wrong_user_id(self):
        user1 = self.create_user("user1")
        user2 = self.create_user("user2")
        self.instance.text = "Existing revision"
        revision1 = self.instance.save_revision(user=user1)
        self.assertEqual(self.instance.revisions.count(), 1)
        self.instance.text = "Updated revision"
        with self.assertRaisesMessage(
            PermissionDenied,
            "Cannot overwrite a revision that was not created by the current user.",
        ):
            self.instance.save_revision(overwrite_revision=revision1, user=user2)

        self.assertEqual(self.instance.revisions.count(), 1)
        latest_revision = self.instance.get_latest_revision()
        self.assertEqual(latest_revision.content["text"], "Existing revision")

    def test_cannot_overwrite_revision_with_omitted_user_id(self):
        user1 = self.create_user("user1")
        self.instance.text = "Existing revision"
        revision1 = self.instance.save_revision(user=user1)
        self.assertEqual(self.instance.revisions.count(), 1)
        self.instance.text = "Updated revision"
        with self.assertRaisesMessage(
            PermissionDenied,
            "Cannot overwrite a revision that was not created by the current user.",
        ):
            self.instance.save_revision(overwrite_revision=revision1)

        self.assertEqual(self.instance.revisions.count(), 1)
        latest_revision = self.instance.get_latest_revision()
        self.assertEqual(latest_revision.content["text"], "Existing revision")

    def test_cannot_overwrite_anonymous_revision_with_user_id(self):
        user1 = self.create_user("user1")
        self.instance.text = "Existing revision"
        revision1 = self.instance.save_revision()
        self.assertEqual(self.instance.revisions.count(), 1)
        self.instance.text = "Updated revision"
        with self.assertRaisesMessage(
            PermissionDenied,
            "Cannot overwrite a revision that was not created by the current user.",
        ):
            self.instance.save_revision(overwrite_revision=revision1, user=user1)

        self.assertEqual(self.instance.revisions.count(), 1)
        latest_revision = self.instance.get_latest_revision()
        self.assertEqual(latest_revision.content["text"], "Existing revision")
