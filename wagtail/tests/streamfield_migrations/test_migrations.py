import datetime
import json

from django.db.models import F, JSONField
from django.db.models.functions import Cast
from django.test import TestCase
from django.utils import timezone

from wagtail.blocks.migrations.operations import RenameStreamChildrenOperation
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

    def setUp(self):
        instances = [
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

        instances = self.model.objects.all().annotate(
            raw_content=Cast(F("content"), JSONField())
        )

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

        instances = self.model.objects.all().annotate(
            raw_content=Cast(F("content"), JSONField())
        )

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

        instances = self.model.objects.all().annotate(
            raw_content=Cast(F("content"), JSONField())
        )

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
