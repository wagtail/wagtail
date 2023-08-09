import datetime

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from freezegun import freeze_time

from wagtail.models import Page, Revision, get_default_page_content_type
from wagtail.test.testapp.models import (
    RevisableGrandChildModel,
    RevisableModel,
    SimplePage,
)


class TestRevisableModel(TestCase):
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
