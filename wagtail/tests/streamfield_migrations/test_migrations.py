import datetime
import json

from django.db import connection
from django.db.models import F, JSONField, TextField
from django.db.models.functions import Cast
from django.test import TestCase
from django.utils import timezone

from wagtail.blocks.migrations.operations import (
    RenameStreamChildrenOperation,
    StreamChildrenToListBlockOperation,
)
from wagtail.test.streamfield_migrations import factories, models
from wagtail.test.streamfield_migrations.testutils import MigrationTestMixin

# TODO test multiple operations in one go


class BaseMigrationTest(TestCase, MigrationTestMixin):
    factory = None
    has_revisions = False
    default_operation_and_block_path = [
        (
            RenameStreamChildrenOperation(old_name="char1", new_name="renamed1"),
            "",
        )
    ]
    app_name = None

    def _get_test_instances(self):
        return [
            self.factory(
                content__0__char1="Test char 1",
                content__1__char1="Test char 2",
                content__2__char2="Test char 3",
                content__3__char2="Test char 4",
            ),
            self.factory(
                content__0__char1="Test char 1",
                content__1__char1="Test char 2",
                content__2__char2="Test char 3",
            ),
            self.factory(
                content__0__char2="Test char 1",
                content__1__char2="Test char 2",
                content__2__char2="Test char 3",
            ),
        ]

    def setUp(self):
        instances = self._get_test_instances()

        self.original_raw_data = {}
        self.original_revisions = {}

        for instance in instances:
            self.original_raw_data[instance.id] = instance.content.raw_data

            if self.has_revisions:
                for i in range(5):
                    revision = instance.save_revision()
                    revision.created_at = timezone.now() - datetime.timedelta(
                        days=(5 - i)
                    )
                    revision.save()
                    if i == 1:
                        instance.live_revision = revision
                        instance.save()
                self.original_revisions[instance.id] = list(
                    instance.revisions.all().order_by("id")
                )

    def assertBlocksRenamed(self, old_content, new_content, is_altered=True):
        for old_block, new_block in zip(old_content, new_content):
            self.assertEqual(old_block["id"], new_block["id"])
            if is_altered and old_block["type"] == "char1":
                self.assertEqual(new_block["type"], "renamed1")
            else:
                self.assertEqual(old_block["type"], new_block["type"])

    def _test_migrate_stream_data(self):
        """Test whether the stream data of the model instances have been updated properly

        Apply the migration and then query the raw data of the updated instances. Compare with
        original raw data and check whether all relevant `char1` blocks have been renamed and
        whether ids and other block types are intact.
        """

        self.apply_migration()

        instances = self.model.objects.all().annotate(
            raw_content=Cast(F("content"), JSONField())
        )

        for instance in instances:
            prev_content = self.original_raw_data[instance.id]
            self.assertBlocksRenamed(
                old_content=prev_content, new_content=instance.raw_content
            )

    # TODO test multiple operations applied in one migration

    def _test_migrate_revisions(self):
        """Test whether all revisions have been updated properly

        Applying migration with `revisions_from=None`, so all revisions should be updated.
        """

        self.apply_migration()

        instances = self.model.objects.all()

        for instance in instances:
            old_revisions = self.original_revisions[instance.id]
            for old_revision, new_revision in zip(
                old_revisions, instance.revisions.all().order_by("id")
            ):
                old_content = json.loads(old_revision.content["content"])
                new_content = json.loads(new_revision.content["content"])
                self.assertBlocksRenamed(
                    old_content=old_content, new_content=new_content
                )

    def _test_always_migrate_live_and_latest_revisions(self):
        """Test whether latest and live revisions are always updated

        Applying migration with `revisions_from` set to a date in the future, so there should be
        no revisions which are made after the date. Only the live and latest revisions should
        update in this case.
        """

        revisions_from = timezone.now() + datetime.timedelta(days=2)
        self.apply_migration(revisions_from=revisions_from)

        instances = self.model.objects.all()

        for instance in instances:
            old_revisions = self.original_revisions[instance.id]
            for old_revision, new_revision in zip(
                old_revisions, instance.revisions.all().order_by("id")
            ):
                is_latest_or_live = old_revision.id == instance.live_revision_id or (
                    old_revision.id == instance.latest_revision_id
                )
                old_content = json.loads(old_revision.content["content"])
                new_content = json.loads(new_revision.content["content"])
                self.assertBlocksRenamed(
                    old_content=old_content,
                    new_content=new_content,
                    is_altered=is_latest_or_live,
                )

    def _test_migrate_revisions_from_date(self):
        """Test whether revisions from a given date onwards are updated

        Applying migration with `revisions_from` set to a date between the created date of the first
        and last revision, so only the revisions after the date and the live and latest revision
        should be updated.
        """

        revisions_from = timezone.now() - datetime.timedelta(days=2)
        self.apply_migration(revisions_from=revisions_from)

        instances = self.model.objects.all()

        for instance in instances:
            old_revisions = self.original_revisions[instance.id]
            for old_revision, new_revision in zip(
                old_revisions, instance.revisions.all().order_by("id")
            ):
                is_latest_or_live = old_revision.id == instance.live_revision_id or (
                    old_revision.id == instance.latest_revision_id
                )
                is_after_revisions_from = old_revision.created_at > revisions_from
                is_altered = is_latest_or_live or is_after_revisions_from
                old_content = json.loads(old_revision.content["content"])
                new_content = json.loads(new_revision.content["content"])
                self.assertBlocksRenamed(
                    old_content=old_content,
                    new_content=new_content,
                    is_altered=is_altered,
                )


class TestNonPageModelWithoutRevisions(BaseMigrationTest):
    model = models.SampleModel
    factory = factories.SampleModelFactory
    has_revisions = False
    app_name = "streamfield_migration_tests"

    def test_migrate_stream_data(self):
        self._test_migrate_stream_data()


class TestPage(BaseMigrationTest):
    model = models.SamplePage
    factory = factories.SamplePageFactory
    has_revisions = True
    app_name = "streamfield_migration_tests"

    def test_migrate_stream_data(self):
        self._test_migrate_stream_data()

    def test_migrate_revisions(self):
        self._test_migrate_revisions()

    def test_always_migrate_live_and_latest_revisions(self):
        self._test_always_migrate_live_and_latest_revisions()

    def test_migrate_revisions_from_date(self):
        self._test_migrate_revisions_from_date()


class TestNullStreamField(BaseMigrationTest):
    """
    Migrations are processed if the underlying JSON is null.

    This might occur if we're operating on a StreamField that was added to a model that
    had existing records.
    """

    model = models.SamplePage
    factory = factories.SamplePageFactory
    has_revisions = True
    app_name = "streamfield_migration_tests"

    def _get_test_instances(self):
        return self.factory.create_batch(1, content=None)

    def setUp(self):
        super().setUp()

        # Bypass StreamField/StreamBlock processing that cast a None stream field value
        # to the empty StreamValue, and set the underlying JSON to null.
        with connection.cursor() as cursor:
            cursor.execute(f"UPDATE {self.model._meta.db_table} SET content = 'null'")

    def assert_null_content(self):
        """
        The raw JSON of all instances for this test is null.
        """

        instances = self.model.objects.all().annotate(
            raw_content=Cast(F("content"), TextField())
        )

        for instance in instances:
            with self.subTest(instance=instance):
                self.assertEqual(instance.raw_content, "null")

    def test_migrate_stream_data(self):
        self.assert_null_content()
        self.apply_migration()
        self.assert_null_content()


class StreamChildrenToListBlockOperationTestCase(BaseMigrationTest):
    model = models.SamplePage
    factory = factories.SamplePageFactory
    has_revisions = True
    app_name = "streamfield_migration_tests"

    def _get_test_instances(self):
        return self.factory.create_batch(
            size=3,
            # Each content stream field has a single char block instance.
            content__0__char1__value="Char Block 1",
        )

    def test_state_not_shared_across_instances(self):
        """
        StreamChildrenToListBlockOperation doesn't share state across model instances.

        As a single operation instance is used to transform the data of multiple model
        instances, we should not store model instance state on the operation instance.
        See https://github.com/wagtail/wagtail/issues/12391.
        """

        self.apply_migration(
            operations_and_block_paths=[
                (
                    StreamChildrenToListBlockOperation(
                        block_name="char1", list_block_name="list1"
                    ),
                    "",
                )
            ]
        )
        for instance in self.model.objects.all().annotate(
            raw_content=Cast(F("content"), JSONField())
        ):
            new_block = instance.raw_content[0]
            self.assertEqual(new_block["type"], "list1")
            self.assertEqual(len(new_block["value"]), 1)
            self.assertEqual(new_block["value"][0]["type"], "item")
            self.assertEqual(new_block["value"][0]["value"], "Char Block 1")
