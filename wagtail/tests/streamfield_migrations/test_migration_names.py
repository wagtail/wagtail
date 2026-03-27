from django.test import TestCase

from wagtail.blocks.migrations.operations import (
    BaseBlockOperation,
    RemoveStreamChildrenOperation,
    RenameStreamChildrenOperation,
)
from wagtail.test.streamfield_migrations import models
from wagtail.test.streamfield_migrations.testutils import MigrationTestMixin


class MigrationNameTest(TestCase, MigrationTestMixin):
    model = models.SamplePage
    app_name = "wagtail_streamfield_migration_toolkit_test"

    def test_rename(self):
        operations_and_block_paths = [
            (
                RenameStreamChildrenOperation(old_name="char1", new_name="renamed1"),
                "",
            )
        ]
        migration = self.init_migration(
            operations_and_block_paths=operations_and_block_paths
        )

        suggested_name = migration.suggest_name()
        self.assertEqual(suggested_name, "rename_char1_to_renamed1")

    def test_remove(self):
        operations_and_block_paths = [
            (
                RemoveStreamChildrenOperation(name="char1"),
                "",
            )
        ]
        migration = self.init_migration(
            operations_and_block_paths=operations_and_block_paths
        )

        suggested_name = migration.suggest_name()
        self.assertEqual(suggested_name, "remove_char1")

    def test_multiple(self):
        operations_and_block_paths = [
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
            operations_and_block_paths=operations_and_block_paths
        )

        suggested_name = migration.suggest_name()
        self.assertEqual(suggested_name, "rename_char1_to_renamed1_remove_char1")

    def test_custom_operation_uses_default_fragment(self):
        class SimpleCustomOperation(BaseBlockOperation):
            def apply(self, block_value):
                return block_value

        operations_and_block_paths = [(SimpleCustomOperation(), "")]
        migration = self.init_migration(
            operations_and_block_paths=operations_and_block_paths
        )

        suggested_name = migration.suggest_name()
        self.assertEqual(suggested_name, "simple_custom_operation")

    def test_custom_operation_can_override_fragment(self):
        class CustomNamedOperation(BaseBlockOperation):
            def apply(self, block_value):
                return block_value

            @property
            def operation_name_fragment(self):
                return "custom_name"

        operations_and_block_paths = [(CustomNamedOperation(), "")]
        migration = self.init_migration(
            operations_and_block_paths=operations_and_block_paths
        )

        suggested_name = migration.suggest_name()
        self.assertEqual(suggested_name, "custom_name")
