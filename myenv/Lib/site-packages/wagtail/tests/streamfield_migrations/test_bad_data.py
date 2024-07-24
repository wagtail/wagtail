import datetime

from django.test import TestCase
from django.utils import timezone

from wagtail.blocks import StreamValue
from wagtail.blocks.migrations import migrate_operation
from wagtail.blocks.migrations.operations import (
    RenameStreamChildrenOperation,
    RenameStructChildrenOperation,
)
from wagtail.blocks.migrations.utils import (
    InvalidBlockDefError,
    apply_changes_to_raw_data,
)
from wagtail.signal_handlers import disable_reference_index_auto_update
from wagtail.test.streamfield_migrations import factories, models
from wagtail.test.streamfield_migrations.testutils import MigrationTestMixin


class TestExceptionRaisedInRawData(TestCase):
    """Directly test whether an exception is raised by apply_changes_to_raw_data for invalid defs.

    This would happen in a situation where the user gives a block path which contains a block name
    which is not present in the block definition in the project state at which the migration is
    applied. (There should also be a block in the stream data with the said name for this to happen)
    """

    def setUp(self):
        raw_data = factories.SampleModelFactory(
            content__0__char1__value="Char Block 1",
            content__1="nestedstruct",
        ).content.raw_data
        raw_data.extend(
            [
                {
                    "type": "invalid_name1",
                    "id": "0001",
                    "value": {"char1": "foo", "char2": "foo"},
                },
                {
                    "type": "invalid_name1",
                    "id": "0002",
                    "value": {"char1": "foo", "char2": "foo"},
                },
            ]
        )
        raw_data[1]["value"]["invalid_name2"] = [
            {"type": "char1", "value": "foo", "id": "0003"}
        ]
        self.raw_data = raw_data

    def test_rename_invalid_stream_child(self):
        """Test whether Exception is raised in when recursing through stream block data"""

        with self.assertRaisesMessage(
            InvalidBlockDefError, "No current block def named invalid_name1"
        ):
            apply_changes_to_raw_data(
                raw_data=self.raw_data,
                block_path_str="invalid_name1",
                operation=RenameStructChildrenOperation(
                    old_name="char1", new_name="renamed1"
                ),
                streamfield=models.SampleModel.content,
            )

    def test_rename_invalid_struct_child(self):
        """Test whether Exception is raised in when recursing through struct block data"""

        with self.assertRaisesMessage(
            InvalidBlockDefError, "No current block def named invalid_name2"
        ):
            apply_changes_to_raw_data(
                raw_data=self.raw_data,
                block_path_str="nestedstruct.invalid_name2",
                operation=RenameStreamChildrenOperation(
                    old_name="char1", new_name="renamed1"
                ),
                streamfield=models.SampleModel.content,
            )


class BadDataMigrationTestCase(TestCase, MigrationTestMixin):
    model = models.SamplePage
    default_operation_and_block_path = [
        (
            RenameStructChildrenOperation(old_name="char1", new_name="renamed1"),
            "invalid_name1",
        )
    ]
    app_name = "streamfield_migration_tests"

    def create_instance(self):
        instance = factories.SamplePageFactory(
            content__0__char1__value="Char Block 1",
            content__1="nestedstruct",
        )
        self.instance = instance

    def append_invalid_instance_data(self):
        raw_data = self.instance.content.raw_data
        raw_data.extend(
            [
                {
                    "type": "invalid_name1",
                    "id": "0001",
                    "value": {"char1": "foo", "char2": "foo"},
                },
                {
                    "type": "invalid_name1",
                    "id": "0002",
                    "value": {"char1": "foo", "char2": "foo"},
                },
            ]
        )
        stream_block = self.instance.content.stream_block
        self.instance.content = StreamValue(
            stream_block=stream_block, stream_data=raw_data, is_lazy=True
        )
        self.instance.save()

    def create_invalid_revision(self, delta):
        self.append_invalid_instance_data()
        invalid_revision = self.create_revision(delta)

        # remove the invalid data from the instance
        raw_data = self.instance.content.raw_data
        raw_data = raw_data[:2]
        stream_block = self.instance.content.stream_block
        self.instance.content = StreamValue(
            stream_block=stream_block, stream_data=raw_data, is_lazy=True
        )
        self.instance.save()

        return invalid_revision.id, invalid_revision.created_at

    def create_revision(self, delta):
        revision = self.instance.save_revision()
        revision.created_at = timezone.now() - datetime.timedelta(days=(delta))
        revision.save()
        return revision


class TestExceptionRaisedForInstance(BadDataMigrationTestCase):
    """Exception should always be raised when applying migration if it occurs while migrating the
    instance data"""

    def setUp(self):
        with disable_reference_index_auto_update():
            self.create_instance()
            self.append_invalid_instance_data()

    def test_migrate(self):
        with self.assertRaisesMessage(
            InvalidBlockDefError,
            "Invalid block def in {} object ({})".format(
                self.instance.__class__.__name__, self.instance.id
            ),
        ):
            self.apply_migration(
                revisions_from=timezone.now() + datetime.timedelta(days=2),
            )


class TestExceptionRaisedForLatestRevision(BadDataMigrationTestCase):
    """Exception should always be raised when applying migration if it occurs while migrating the
    latest revision data"""

    def setUp(self):
        with disable_reference_index_auto_update():
            self.create_instance()

            for i in range(4):
                self.create_revision(5 - i)

            (
                self.invalid_revision_id,
                self.invalid_revision_created_at,
            ) = self.create_invalid_revision(0)

    def test_migrate(self):
        with self.assertRaisesMessage(
            InvalidBlockDefError,
            "Invalid block def in {} object ({}) for revision id ({}) created at {}".format(
                self.instance.__class__.__name__,
                self.instance.id,
                self.invalid_revision_id,
                self.invalid_revision_created_at,
            ),
        ):
            self.apply_migration(revisions_from=None)


class TestExceptionRaisedForLiveRevision(BadDataMigrationTestCase):
    """Exception should always be raised when applying migration if it occurs while migrating the
    live revision data"""

    def setUp(self):
        with disable_reference_index_auto_update():
            self.create_instance()

            (
                self.invalid_revision_id,
                self.invalid_revision_created_at,
            ) = self.create_invalid_revision(5)
            self.instance.live_revision_id = self.invalid_revision_id
            self.instance.save()

            for i in range(1, 5):
                self.create_revision(5 - i)

    def test_migrate(self):
        with self.assertRaisesMessage(
            InvalidBlockDefError,
            "Invalid block def in {} object ({}) for revision id ({}) created at {}".format(
                self.instance.__class__.__name__,
                self.instance.id,
                self.invalid_revision_id,
                self.invalid_revision_created_at,
            ),
        ):
            self.apply_migration(revisions_from=None)


class TestExceptionIgnoredForOtherRevisions(BadDataMigrationTestCase):
    """Exception should not be be raised when applying migration if it occurs while migrating
    revision data which is not of a live or latest revision. Instead an exception should be logged"""

    model = models.SamplePage

    def setUp(self):
        with disable_reference_index_auto_update():
            self.create_instance()
            (
                self.invalid_revision_id,
                self.invalid_revision_created_at,
            ) = self.create_invalid_revision(5)

            for i in range(1, 5):
                self.create_revision(5 - i)

    def test_migrate(self):
        with self.assertLogs(level="ERROR") as cm:
            self.apply_migration(revisions_from=None)

            self.assertEqual(
                cm.output[0].splitlines()[0],
                "ERROR:{}:Invalid block def in {} object ({}) for revision id ({}) created at {}".format(
                    migrate_operation.__name__,
                    self.instance.__class__.__name__,
                    self.instance.id,
                    self.invalid_revision_id,
                    self.invalid_revision_created_at,
                ),
            )

            self.assertEqual(
                cm.output[0].splitlines()[-1],
                "{}: No current block def named invalid_name1".format(
                    InvalidBlockDefError.__module__
                    + "."
                    + InvalidBlockDefError.__name__
                ),
            )
