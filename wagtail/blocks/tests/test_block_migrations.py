from django.test import TestCase
from wagtail.blocks.migrations.operations import (
    RenameStreamChildrenOperation,
    RenameStructChildrenOperation,
    RemoveStreamChildrenOperation,
    StreamChildrenToStructBlockOperation
)

class TestBlockMigrations(TestCase):
    def test_rename_stream_children(self):
        op = RenameStreamChildrenOperation("char1", "title")
        block_value = [{"type": "char1", "value": "Hello", "id": "123"}]
        
        # Forward
        applied = op.apply(block_value)
        self.assertEqual(applied[0]["type"], "title")
        # Backward
        reversed_data = op.reverse(applied)
        self.assertEqual(reversed_data[0]["type"], "char1")

    def test_rename_struct_children(self):
        op = RenameStructChildrenOperation("old_field", "new_field")
        # Note: StructBlock values are DICTS, not lists
        block_value = {"old_field": "some value", "other_field": "stays"}
        
        applied = op.apply(block_value)
        self.assertIn("new_field", applied)
        self.assertNotIn("old_field", applied)
        self.assertEqual(applied["new_field"], "some value")

    def test_remove_stream_children(self):
        op = RemoveStreamChildrenOperation("delete_me")
        block_value = [
            {"type": "keep_me", "value": "A"},
            {"type": "delete_me", "value": "B"}
        ]
        applied = op.apply(block_value)
        self.assertEqual(len(applied), 1)
        self.assertEqual(applied[0]["type"], "keep_me")

    def test_stream_children_to_struct_block(self):
        # Testing the 'wrapping' logic
        op = StreamChildrenToStructBlockOperation("item", "wrapper")
        block_value = [{"type": "item", "value": "Inner Value", "id": "1"}]
        
        applied = op.apply(block_value)
        # Expected: [{'type': 'wrapper', 'value': {'item': 'Inner Value'}, 'id': '1'}]
        self.assertEqual(applied[0]["type"], "wrapper")
        self.assertEqual(applied[0]["value"]["item"], "Inner Value")
