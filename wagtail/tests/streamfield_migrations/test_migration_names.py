from django.test import TestCase

from wagtail.blocks.migrations.operations import (
    RemoveStreamChildrenOperation,
    RenameStreamChildrenOperation,
)
from wagtail.test.streamfield_migrations import models
from wagtail.test.streamfield_migrations.testutils import MigrationTestMixin


class MigrationNameTest(TestCase, MigrationTestMixin):
    model = models.SamplePage
    app_name = "wagtail_streamfield_migration_toolkit_test"

    def test_rename(self):
        operations_and_block_path = [
            (
                RenameStreamChildrenOperation(old_name="char1", new_name="renamed1"),
                "",
            )
        ]
        migration = self.init_migration(
            operations_and_block_path=operations_and_block_path
        )

        suggested_name = migration.suggest_name()
        self.assertEqual(suggested_name, "rename_char1_to_renamed1")

    def test_remove(self):
        operations_and_block_path = [
            (
                RemoveStreamChildrenOperation(name="char1"),
                "",
            )
        ]
        migration = self.init_migration(
            operations_and_block_path=operations_and_block_path
        )

        suggested_name = migration.suggest_name()
        self.assertEqual(suggested_name, "remove_char1")

    def test_multiple(self):
        operations_and_block_path = [
            (
                RenameStreamChildrenOperation(old_name="char1", new_name="renamed1"),
                "",
            ),
            (
                RemoveStreamChildrenOperation(name="char1"),
                "simplestruct",
            ),
        ]
        migration = self.init_migration(
            operations_and_block_path=operations_and_block_path
        )

        suggested_name = migration.suggest_name()
        self.assertEqual(suggested_name, "rename_char1_to_renamed1_remove_char1")
